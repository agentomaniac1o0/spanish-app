"""
Word image generation via RunPod Serverless ComfyUI for Spanish learning app.
One function: generate_word_image(spanish_word, german_word, word_id) -> bool
"""
import base64
import logging
import os
import random
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RUNPOD_JUGGERNAUT_ID = os.getenv("RUNPOD_JUGGERNAUT_ID", "")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
JUGGERNAUT_URL = f"https://api.runpod.ai/v2/{RUNPOD_JUGGERNAUT_ID}/runsync" if RUNPOD_JUGGERNAUT_ID else ""

NEXTCLOUD_HOST = os.getenv("NEXTCLOUD_HOST", "")
NEXTCLOUD_USER = os.getenv("NEXTCLOUD_USER", "")
NEXTCLOUD_APP_PASSWORD = os.getenv("NEXTCLOUD_APP_PASSWORD", "")
STOCK_UPLOAD_PATH = "Home Lab/Spanish App/Wortbilder"

STATIC_DIR = Path(os.getenv("STATIC_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "static")))

HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}

_spain_prompts = [
    "A clean, simple educational illustration of '{spanish}' ({german}), white background, flat vector style, no text, colorful",
    "Minimalist cartoon showing '{spanish}' ({german}), white backdrop, simple shapes, teaching material style, no letters",
    "Bright cute illustration depicting '{spanish}' ({german}), isolated on white, children's book style, no words or text",
    "Simple colorful icon-style drawing representing '{spanish}' ({german}), clean white background, clipart, no text",
]


def _build_workflow(prompt: str) -> dict:
    seed = random.randint(1, 2**32 - 1)
    neg = "ugly, blurry, low quality, watermark, text, letters, words, nsfw, deformed, photorealistic, photo"
    return {
        "3": {"inputs": {"seed": seed, "steps": 8, "cfg": 2.0, "sampler_name": "lcm", "scheduler": "normal",
                          "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0],
                          "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
        "4": {"inputs": {"ckpt_name": "DreamShaper8_LCM.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": 768, "height": 768, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": neg, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "spanish_word", "images": ["8", 0]}, "class_type": "SaveImage"},
    }


def _build_upscale_workflow() -> dict:
    return {
        "1": {"inputs": {"image": "input_base.png"}, "class_type": "LoadImage"},
        "10": {"inputs": {"model_name": "4x-UltraSharp.pth"}, "class_type": "UpscaleModelLoader"},
        "11": {"inputs": {"upscale_model": ["10", 0], "image": ["1", 0]}, "class_type": "ImageUpscaleWithModel"},
        "12": {"inputs": {"filename_prefix": "stock_upscaled", "images": ["11", 0]}, "class_type": "SaveImage"},
    }


def _call_serverless(workflow: dict, image_input: dict = None, timeout: int = 120) -> str | None:
    """Call RunPod serverless, return base64 image data or None."""
    if not JUGGERNAUT_URL or not RUNPOD_API_KEY:
        logger.error("RunPod config missing")
        return None
    try:
        payload = {"input": {"workflow": workflow}}
        if image_input:
            payload["input"]["images"] = [image_input]
        resp = httpx.post(JUGGERNAUT_URL, json=payload, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            logger.error("Serverless error %d: %s", resp.status_code, resp.text[:200])
            return None
        data = resp.json()
        images = data.get("output", {}).get("images", [])
        if not images:
            logger.error("No images in output")
            return None
        img_data = images[0].get("data", "")
        if not img_data:
            logger.error("No image data field")
            return None
        return img_data
    except Exception as e:
        logger.error("Serverless failed: %s", e)
        return None


def _save_base64(b64_data: str, path: str) -> bool:
    try:
        if b64_data.startswith("data:"):
            b64_data = b64_data.split(",", 1)[1]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64_data))
        logger.info("Saved: %s", path)
        return True
    except Exception as e:
        logger.error("Save failed: %s", e)
        return False


def _upload_to_nextcloud(local_path: str, filename: str) -> bool:
    if not NEXTCLOUD_HOST or not NEXTCLOUD_USER or not NEXTCLOUD_APP_PASSWORD:
        logger.warning("Nextcloud not configured")
        return False
    try:
        from urllib.parse import quote
        encoded = quote(filename)
        url = f"{NEXTCLOUD_HOST}/remote.php/dav/files/{NEXTCLOUD_USER}/{STOCK_UPLOAD_PATH}/{encoded}"
        with open(local_path, "rb") as f:
            resp = httpx.put(url, content=f.read(), auth=(NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD), timeout=60, verify=False)
        if resp.status_code in (200, 201, 204):
            logger.info("Nextcloud: %s uploaded", filename)
            return True
        if resp.status_code == 409:
            parent = f"{NEXTCLOUD_HOST}/remote.php/dav/files/{NEXTCLOUD_USER}/{STOCK_UPLOAD_PATH}"
            httpx.request("MKCOL", parent, auth=(NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD), timeout=10, verify=False)
            with open(local_path, "rb") as f:
                resp = httpx.put(url, content=f.read(), auth=(NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD), timeout=60, verify=False)
            if resp.status_code in (200, 201, 204):
                logger.info("Nextcloud: %s uploaded after MKCOL", filename)
                return True
        logger.error("Nextcloud upload failed: %d", resp.status_code)
        return False
    except Exception as e:
        logger.error("Nextcloud error: %s", e)
        return False


def word_image_exists(word_id: int) -> bool:
    return (STATIC_DIR / "words" / f"word_{word_id}.jpg").exists()


def generate_word_image(word_id: int, spanish: str, german: str, upload_stock: bool = True) -> bool:
    """
    Generate an image for a Spanish vocabulary word via RunPod serverless.
    Two-pass: base image (DreamShaper) then 4x-UltraSharp upscale for stock.
    Base image is saved to static/words/word_{id}.jpg.
    Returns True if base image was generated successfully.
    """
    prompt = random.choice(_spain_prompts).format(spanish=spanish, german=german)
    logger.info("Generating image for word %d: %s (%s)", word_id, spanish, german)

    base_data = _call_serverless(_build_workflow(prompt), timeout=120)
    if not base_data:
        return False

    words_dir = STATIC_DIR / "words"
    os.makedirs(str(words_dir), exist_ok=True)
    base_path = str(words_dir / f"word_{word_id}.jpg")

    if not _save_base64(base_data, base_path):
        return False

    if upload_stock:
        ts = int(time.time())
        up_data = _call_serverless(
            _build_upscale_workflow(),
            image_input={"name": "input_base.png", "image": base_data},
            timeout=120,
        )
        if up_data:
            stock_path = str(words_dir / f"word_{word_id}_stock.png")
            if _save_base64(up_data, stock_path):
                stock_name = f"word_{word_id}_{spanish}_{ts}.png"
                _upload_to_nextcloud(stock_path, stock_name)

    return True
