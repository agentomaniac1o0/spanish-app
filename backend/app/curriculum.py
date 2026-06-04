"""
Curriculum seed data: words, lessons, grammar points, placement test.
Imported and seeded into the database on first startup.
"""

GRAMMAR_POINTS = [
    # A0
    {"title": "Das spanische Alphabet", "level": "A0", "sort_order": 1,
     "explanation": "Das spanische Alphabet hat 27 Buchstaben: a, b, c, d, e, f, g, h, i, j, k, l, m, n, ñ, o, p, q, r, s, t, u, v, w, x, y, z. "
                    "Besonderheiten: ñ (eñe), ll (elle, bis 2010 eigener Buchstabe), rr (doppeltes gerolltes R). "
                    "Vokale werden immer gleich ausgesprochen: a (wie in 'Mama'), e (wie in 'Fee'), i (wie 'ie'), o (offen), u (wie 'uh').",
     "examples_json": '[{"spanish":"hola","german":"hallo"},{"spanish":"adiós","german":"tschüss"},{"spanish":"gracias","german":"danke"},{"spanish":"por favor","german":"bitte"},{"spanish":"sí","german":"ja"},{"spanish":"no","german":"nein"}]'},
    {"title": "Zahlen 1-20", "level": "A0", "sort_order": 2,
     "explanation": "Grundzahlen auf Spanisch: uno, dos, tres, cuatro, cinco, seis, siete, ocho, nueve, diez, once, doce, trece, catorce, quince, dieciséis, diecisiete, dieciocho, diecinueve, veinte. "
                    "Ab 16 werden die Zahlen zusammengesetzt (diez + y + seis = dieciséis).",
     "examples_json": '[{"spanish":"uno","german":"eins"},{"spanish":"cinco","german":"fünf"},{"spanish":"diez","german":"zehn"},{"spanish":"quince","german":"fünfzehn"},{"spanish":"veinte","german":"zwanzig"}]'},
    {"title": "Farben", "level": "A0", "sort_order": 3,
     "explanation": "Farben sind Adjektive und passen sich in Zahl und Geschlecht an das Nomen an. "
                    "rojo/roja (rot), azul (blau), verde (grün), amarillo/amarilla (gelb), blanco/blanca (weiß), negro/negra (schwarz), naranja (orange), gris (grau), marrón (braun), rosa (rosa). "
                    "Einige Farben wie azul und verde sind unveränderlich.",
     "examples_json": '[{"spanish":"El coche es rojo.","german":"Das Auto ist rot."},{"spanish":"La casa es blanca.","german":"Das Haus ist weiß."},{"spanish":"El cielo es azul.","german":"Der Himmel ist blau."}]'},

    # A1
    {"title": "Ser vs Estar", "level": "A1", "sort_order":4,
     "explanation": "Beide bedeuten 'sein', aber mit unterschiedlicher Verwendung. SER für dauerhafte Eigenschaften: Identität, Herkunft, Beruf, Charakter, Zeit, Farbe, Material. "
                    "ESTAR für Zustände: Ort, Befinden, Gesundheit, vorübergehende Eigenschaften, Verlaufsform (estar + gerundio). "
                    "Beispiele: Soy alemán (Ich bin Deutscher) vs Estoy en Madrid (Ich bin in Madrid). Soy médico (Beruf) vs Estoy cansado (Zustand).",
     "examples_json": '[{"spanish":"Soy profesor.","german":"Ich bin Lehrer."},{"spanish":"Estoy feliz.","german":"Ich bin glücklich."},{"spanish":"La puerta está abierta.","german":"Die Tür ist offen."},{"spanish":"Ella es mi hermana.","german":"Sie ist meine Schwester."}]'},
    {"title": "Por vs Para", "level": "A1", "sort_order":5,
     "explanation": "POR: Grund/Ursache (por qué = warum), Dauer (por dos horas), ungefähre Ortsangabe (por aquí), Tausch (gracias por...), Preis, "
                    "Mittel/Medium (por teléfono), Agent im Passiv. "
                    "PARA: Ziel/Zweck (para qué = wozu), Empfänger (para ti = für dich), Deadline (para mañana), "
                    "Richtung (salgo para Madrid), Meinung (para mí...), Vergleich (para su edad).",
     "examples_json": '[{"spanish":"Gracias por tu ayuda.","german":"Danke für deine Hilfe."},{"spanish":"Este regalo es para ti.","german":"Dieses Geschenk ist für dich."},{"spanish":"Estudio español por dos horas.","german":"Ich lerne zwei Stunden Spanisch."},{"spanish":"Salgo para Barcelona mañana.","german":"Ich fahre morgen nach Barcelona."}]'},
    {"title": "Bestimmte und unbestimmte Artikel", "level": "A1", "sort_order":6,
     "explanation": "Bestimmt (der/die/das): el (m.sg), la (f.sg), los (m.pl), las (f.pl). "
                    "Unbestimmt (ein/eine): un (m.sg), una (f.sg), unos (m.pl ~ einige), unas (f.pl ~ einige). "
                    "Regeln: Männlich meist -o, weiblich meist -a. Ausnahmen: el día (m), la mano (f), el problema (m, griechisch -ma).",
     "examples_json": '[{"spanish":"el libro","german":"das Buch"},{"spanish":"la mesa","german":"der Tisch"},{"spanish":"los amigos","german":"die Freunde"},{"spanish":"un coche","german":"ein Auto"},{"spanish":"una casa","german":"ein Haus"}]'},
    {"title": "Hay und Estar für Orte", "level": "A1", "sort_order":7,
     "explanation": "HAY (es gibt) wird für die Existenz oder das Vorhandensein von etwas verwendet. Kein bestimmter Artikel nach hay! "
                    "ESTAR wird für die Position von bestimmten Dingen oder Personen verwendet. "
                    "Hay un libro en la mesa (Es gibt ein Buch auf dem Tisch). El libro está en la mesa (Das Buch ist auf dem Tisch).",
     "examples_json": '[{"spanish":"Hay un restaurante cerca.","german":"Es gibt ein Restaurant in der Nähe."},{"spanish":"El restaurante está en la calle Mayor.","german":"Das Restaurant ist in der Hauptstraße."},{"spanish":"¿Hay un banco por aquí?","german":"Gibt es hier eine Bank?"}]'},

    # A2
    {"title": "Pretérito Indefinido", "level": "A2", "sort_order":8,
     "explanation": "Das Pretérito Indefinido (einfache Vergangenheit) beschreibt abgeschlossene Handlungen in der Vergangenheit. "
                    "Regelmäßige Verben: -ar → -é, -aste, -ó, -amos, -asteis, -aron (hablar → hablé). "
                    "-er/-ir → -í, -iste, -ió, -imos, -isteis, -ieron (comer → comí). "
                    "Signalwörter: ayer (gestern), la semana pasada (letzte Woche), en 2020, hace dos días (vor zwei Tagen).",
     "examples_json": '[{"spanish":"Ayer comí paella.","german":"Gestern aß ich Paella."},{"spanish":"Viajé a México en 2020.","german":"Ich reiste 2020 nach Mexiko."},{"spanish":"Estudiamos español la semana pasada.","german":"Wir lernten letzte Woche Spanisch."},{"spanish":"¿Dónde naciste?","german":"Wo bist du geboren?"}]'},
    {"title": "Pretérito Imperfecto", "level": "A2", "sort_order":9,
     "explanation": "Das Imperfecto beschreibt Gewohnheiten, wiederholte Handlungen, Hintergrundbeschreibungen und gleichzeitige Handlungen in der Vergangenheit. "
                    "-ar → -aba, -abas, -aba, -ábamos, -abais, -aban. "
                    "-er/-ir → -ía, -ías, -ía, -íamos, -íais, -ían. "
                    "Nur drei unregelmäßige: ser → era, ir → iba, ver → veía. "
                    "Signalwörter: siempre (immer), todos los días (jeden Tag), antes (früher), mientras (während).",
     "examples_json": '[{"spanish":"Cuando era niño, vivía en Madrid.","german":"Als ich Kind war, lebte ich in Madrid."},{"spanish":"Siempre íbamos a la playa en verano.","german":"Wir gingen im Sommer immer an den Strand."},{"spanish":"Llovía mientras caminaba.","german":"Es regnete während ich ging."}]'},
    {"title": "Gustar und ähnliche Verben", "level": "A2", "sort_order":10,
     "explanation": "Gustar (gefallen) funktioniert anders als im Deutschen: Das Subjekt ist die Sache, die gefällt. "
                    "Me gusta el café (Kaffee gefällt mir = Ich mag Kaffee). Me gustan los perros (Hunde gefallen mir). "
                    "Pronomen: me, te, le, nos, os, les. "
                    "Ähnliche Verben: encantar (begeistern), interesar (interessieren), importar (wichtig sein), doler (schmerzen), parecer (erscheinen).",
     "examples_json": '[{"spanish":"Me gusta la música.","german":"Ich mag Musik."},{"spanish":"Te gustan los gatos.","german":"Du magst Katzen."},{"spanish":"Nos encanta viajar.","german":"Wir lieben es zu reisen."},{"spanish":"¿Te interesa el arte?","german":"Interessiert dich Kunst?"}]'},

    # B1
    {"title": "Subjuntivo Presente", "level": "B1", "sort_order":11,
     "explanation": "Der Subjuntivo drückt Wunsch, Zweifel, Gefühle, Unsicherheit und subjektive Bewertung aus. "
                    "Bildung: Stamm der 1. Person Präsens Indikativ minus -o + Subjuntivo-Endung. "
                    "-ar → -e, -es, -e, -emos, -éis, -en. -er/-ir → -a, -as, -a, -amos, -áis, -an. "
                    "Auslöser: ojalá (hoffentlich), quiero que (ich will dass), es importante que, dudo que (ich bezweifle dass), "
                    "antes de que (bevor), para que (damit), aunque + subj (auch wenn).",
     "examples_json": '[{"spanish":"Quiero que vengas a la fiesta.","german":"Ich will, dass du zur Party kommst."},{"spanish":"Ojalá que llueva mañana.","german":"Hoffentlich regnet es morgen."},{"spanish":"Dudo que sea verdad.","german":"Ich bezweifle, dass es wahr ist."},{"spanish":"Es importante que estudies.","german":"Es ist wichtig, dass du lernst."}]'},
    {"title": "Konditional (Futuro Hipotético)", "level": "B1", "sort_order":12,
     "explanation": "Der Konditional (Condicional Simple) drückt höfliche Bitten, Wünsche, Ratschläge und hypothetische Situationen aus. "
                    "Bildung: Infinitiv + -ía, -ías, -ía, -íamos, -íais, -ían. "
                    "Unregelmäßige Stämme (wie Futur): tener → tendr-, poner → pondr-, salir → saldr-, hacer → har-, decir → dir-, querer → querr-, saber → sabr-, poder → podr-, haber → habr-, caber → cabr-.",
     "examples_json": '[{"spanish":"Me gustaría un café, por favor.","german":"Ich hätte gerne einen Kaffee, bitte."},{"spanish":"¿Podrías ayudarme?","german":"Könntest du mir helfen?"},{"spanish":"Yo en tu lugar, estudiaría más.","german":"An deiner Stelle würde ich mehr lernen."},{"spanish":"Dijo que vendría mañana.","german":"Er sagte, er würde morgen kommen."}]'},
]


WORDS = [
    # === A0 — Basics ===
    {"spanish":"hola","german":"hallo","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"adiós","german":"tschüss","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"buenos días","german":"guten Morgen","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"buenas tardes","german":"guten Tag (Nachmittag)","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"buenas noches","german":"guten Abend / gute Nacht","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"por favor","german":"bitte","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"gracias","german":"danke","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"de nada","german":"gern geschehen","word_type":"phrase","level":"A0","unit":"greetings"},
    {"spanish":"sí","german":"ja","word_type":"adverb","level":"A0","unit":"greetings"},
    {"spanish":"no","german":"nein","word_type":"adverb","level":"A0","unit":"greetings"},
    {"spanish":"uno","german":"eins","word_type":"number","level":"A0","unit":"numbers","example_sentence":"Tengo un hermano.","example_translation":"Ich habe einen Bruder."},
    {"spanish":"dos","german":"zwei","word_type":"number","level":"A0","unit":"numbers"},
    {"spanish":"tres","german":"drei","word_type":"number","level":"A0","unit":"numbers"},
    {"spanish":"cuatro","german":"vier","word_type":"number","level":"A0","unit":"numbers"},
    {"spanish":"cinco","german":"fünf","word_type":"number","level":"A0","unit":"numbers"},
    {"spanish":"diez","german":"zehn","word_type":"number","level":"A0","unit":"numbers"},
    {"spanish":"rojo","german":"rot","word_type":"adjective","level":"A0","unit":"colors","example_sentence":"El tomate es rojo.","example_translation":"Die Tomate ist rot."},
    {"spanish":"azul","german":"blau","word_type":"adjective","level":"A0","unit":"colors"},
    {"spanish":"verde","german":"grün","word_type":"adjective","level":"A0","unit":"colors"},
    {"spanish":"amarillo","german":"gelb","word_type":"adjective","level":"A0","unit":"colors"},
    {"spanish":"blanco","german":"weiß","word_type":"adjective","level":"A0","unit":"colors"},
    {"spanish":"negro","german":"schwarz","word_type":"adjective","level":"A0","unit":"colors"},

    # === A1 — Everyday ===
    {"spanish":"el restaurante","german":"das Restaurant","word_type":"noun","level":"A1","unit":"restaurant","example_sentence":"El restaurante está abierto.","example_translation":"Das Restaurant ist geöffnet."},
    {"spanish":"la mesa","german":"der Tisch","word_type":"noun","level":"A1","unit":"restaurant"},
    {"spanish":"la carta","german":"die Speisekarte","word_type":"noun","level":"A1","unit":"restaurant"},
    {"spanish":"el camarero","german":"der Kellner","word_type":"noun","level":"A1","unit":"restaurant"},
    {"spanish":"la cuenta","german":"die Rechnung","word_type":"noun","level":"A1","unit":"restaurant","example_sentence":"La cuenta, por favor.","example_translation":"Die Rechnung, bitte."},
    {"spanish":"la comida","german":"das Essen","word_type":"noun","level":"A1","unit":"restaurant"},
    {"spanish":"la bebida","german":"das Getränk","word_type":"noun","level":"A1","unit":"restaurant"},
    {"spanish":"pedir","german":"bestellen","word_type":"verb","level":"A1","unit":"restaurant","example_sentence":"Voy a pedir una pizza.","example_translation":"Ich werde eine Pizza bestellen."},
    {"spanish":"comer","german":"essen","word_type":"verb","level":"A1","unit":"restaurant","example_sentence":"Me gusta comer paella.","example_translation":"Ich esse gerne Paella."},
    {"spanish":"beber","german":"trinken","word_type":"verb","level":"A1","unit":"restaurant","example_sentence":"¿Qué quieres beber?","example_translation":"Was möchtest du trinken?"},
    {"spanish":"la tienda","german":"das Geschäft","word_type":"noun","level":"A1","unit":"shopping","example_sentence":"La tienda cierra a las ocho.","example_translation":"Das Geschäft schließt um acht."},
    {"spanish":"comprar","german":"kaufen","word_type":"verb","level":"A1","unit":"shopping","example_sentence":"Voy a comprar pan.","example_translation":"Ich gehe Brot kaufen."},
    {"spanish":"el precio","german":"der Preis","word_type":"noun","level":"A1","unit":"shopping"},
    {"spanish":"caro","german":"teuer","word_type":"adjective","level":"A1","unit":"shopping"},
    {"spanish":"barato","german":"billig","word_type":"adjective","level":"A1","unit":"shopping"},
    {"spanish":"el dinero","german":"das Geld","word_type":"noun","level":"A1","unit":"shopping"},
    {"spanish":"pagar","german":"bezahlen","word_type":"verb","level":"A1","unit":"shopping","example_sentence":"¿Puedo pagar con tarjeta?","example_translation":"Kann ich mit Karte bezahlen?"},
    {"spanish":"la familia","german":"die Familie","word_type":"noun","level":"A1","unit":"family","example_sentence":"Mi familia es grande.","example_translation":"Meine Familie ist groß."},
    {"spanish":"la madre","german":"die Mutter","word_type":"noun","level":"A1","unit":"family"},
    {"spanish":"el padre","german":"der Vater","word_type":"noun","level":"A1","unit":"family"},
    {"spanish":"el hermano","german":"der Bruder","word_type":"noun","level":"A1","unit":"family"},
    {"spanish":"la hermana","german":"die Schwester","word_type":"noun","level":"A1","unit":"family"},
    {"spanish":"el hijo","german":"der Sohn","word_type":"noun","level":"A1","unit":"family"},
    {"spanish":"el tiempo","german":"das Wetter / die Zeit","word_type":"noun","level":"A1","unit":"weather","example_sentence":"¿Qué tiempo hace?","example_translation":"Wie ist das Wetter?"},
    {"spanish":"hace sol","german":"es ist sonnig","word_type":"phrase","level":"A1","unit":"weather"},
    {"spanish":"hace calor","german":"es ist heiß","word_type":"phrase","level":"A1","unit":"weather"},
    {"spanish":"hace frío","german":"es ist kalt","word_type":"phrase","level":"A1","unit":"weather"},
    {"spanish":"llueve","german":"es regnet","word_type":"phrase","level":"A1","unit":"weather"},
    {"spanish":"la hora","german":"die Uhrzeit / Stunde","word_type":"noun","level":"A1","unit":"time","example_sentence":"¿Qué hora es?","example_translation":"Wie spät ist es?"},
    {"spanish":"el día","german":"der Tag","word_type":"noun","level":"A1","unit":"time"},
    {"spanish":"la semana","german":"die Woche","word_type":"noun","level":"A1","unit":"time"},
    {"spanish":"hoy","german":"heute","word_type":"adverb","level":"A1","unit":"time"},
    {"spanish":"mañana","german":"morgen","word_type":"adverb","level":"A1","unit":"time"},
    {"spanish":"ayer","german":"gestern","word_type":"adverb","level":"A1","unit":"time"},

    # === A2 — Travel & Daily Life ===
    {"spanish":"viajar","german":"reisen","word_type":"verb","level":"A2","unit":"travel","example_sentence":"Me encanta viajar por España.","example_translation":"Ich liebe es, durch Spanien zu reisen."},
    {"spanish":"el aeropuerto","german":"der Flughafen","word_type":"noun","level":"A2","unit":"travel"},
    {"spanish":"el hotel","german":"das Hotel","word_type":"noun","level":"A2","unit":"travel"},
    {"spanish":"la habitación","german":"das Zimmer","word_type":"noun","level":"A2","unit":"travel","example_sentence":"Quiero reservar una habitación.","example_translation":"Ich möchte ein Zimmer reservieren."},
    {"spanish":"el billete","german":"die Fahrkarte / das Ticket","word_type":"noun","level":"A2","unit":"travel"},
    {"spanish":"la maleta","german":"der Koffer","word_type":"noun","level":"A2","unit":"travel"},
    {"spanish":"la playa","german":"der Strand","word_type":"noun","level":"A2","unit":"travel","example_sentence":"Vamos a la playa este fin de semana.","example_translation":"Wir gehen dieses Wochenende an den Strand."},
    {"spanish":"la calle","german":"die Straße","word_type":"noun","level":"A2","unit":"directions"},
    {"spanish":"la plaza","german":"der Platz","word_type":"noun","level":"A2","unit":"directions"},
    {"spanish":"la esquina","german":"die Ecke","word_type":"noun","level":"A2","unit":"directions"},
    {"spanish":"derecha","german":"rechts","word_type":"adverb","level":"A2","unit":"directions","example_sentence":"Gira a la derecha.","example_translation":"Biege rechts ab."},
    {"spanish":"izquierda","german":"links","word_type":"adverb","level":"A2","unit":"directions"},
    {"spanish":"todo recto","german":"geradeaus","word_type":"phrase","level":"A2","unit":"directions"},
    {"spanish":"cerca","german":"nah","word_type":"adverb","level":"A2","unit":"directions"},
    {"spanish":"lejos","german":"weit","word_type":"adverb","level":"A2","unit":"directions"},
    {"spanish":"trabajar","german":"arbeiten","word_type":"verb","level":"A2","unit":"work","example_sentence":"Trabajo en una oficina.","example_translation":"Ich arbeite in einem Büro."},
    {"spanish":"el trabajo","german":"die Arbeit","word_type":"noun","level":"A2","unit":"work"},
    {"spanish":"la empresa","german":"das Unternehmen","word_type":"noun","level":"A2","unit":"work"},
    {"spanish":"el jefe","german":"der Chef","word_type":"noun","level":"A2","unit":"work"},
    {"spanish":"la reunión","german":"die Besprechung","word_type":"noun","level":"A2","unit":"work"},
    {"spanish":"ganar","german":"verdienen / gewinnen","word_type":"verb","level":"A2","unit":"work","example_sentence":"¿Cuánto ganas al mes?","example_translation":"Wie viel verdienst du im Monat?"},
    {"spanish":"la cocina","german":"die Küche","word_type":"noun","level":"A2","unit":"home"},
    {"spanish":"el baño","german":"das Badezimmer","word_type":"noun","level":"A2","unit":"home"},
    {"spanish":"la cama","german":"das Bett","word_type":"noun","level":"A2","unit":"home"},
    {"spanish":"la ventana","german":"das Fenster","word_type":"noun","level":"A2","unit":"home"},
    {"spanish":"la puerta","german":"die Tür","word_type":"noun","level":"A2","unit":"home","example_sentence":"Cierra la puerta, por favor.","example_translation":"Schließe bitte die Tür."},
    {"spanish":"el médico","german":"der Arzt","word_type":"noun","level":"A2","unit":"health"},
    {"spanish":"el hospital","german":"das Krankenhaus","word_type":"noun","level":"A2","unit":"health"},
    {"spanish":"la salud","german":"die Gesundheit","word_type":"noun","level":"A2","unit":"health"},
    {"spanish":"enfermo","german":"krank","word_type":"adjective","level":"A2","unit":"health","example_sentence":"Estoy enfermo hoy.","example_translation":"Ich bin heute krank."},
    {"spanish":"el dolor","german":"der Schmerz","word_type":"noun","level":"A2","unit":"health","example_sentence":"Tengo dolor de cabeza.","example_translation":"Ich habe Kopfschmerzen."},

    # === B1 — Intermediate ===
    {"spanish":"el gobierno","german":"die Regierung","word_type":"noun","level":"B1","unit":"news"},
    {"spanish":"la noticia","german":"die Nachricht","word_type":"noun","level":"B1","unit":"news","example_sentence":"¿Has leído las noticias hoy?","example_translation":"Hast du heute die Nachrichten gelesen?"},
    {"spanish":"el periódico","german":"die Zeitung","word_type":"noun","level":"B1","unit":"news"},
    {"spanish":"la economía","german":"die Wirtschaft","word_type":"noun","level":"B1","unit":"news"},
    {"spanish":"el cambio climático","german":"der Klimawandel","word_type":"phrase","level":"B1","unit":"news"},
    {"spanish":"en mi opinión","german":"meiner Meinung nach","word_type":"phrase","level":"B1","unit":"opinions","example_sentence":"En mi opinión, es una buena idea.","example_translation":"Meiner Meinung nach ist es eine gute Idee."},
    {"spanish":"estoy de acuerdo","german":"ich stimme zu","word_type":"phrase","level":"B1","unit":"opinions"},
    {"spanish":"no estoy de acuerdo","german":"ich stimme nicht zu","word_type":"phrase","level":"B1","unit":"opinions"},
    {"spanish":"creo que","german":"ich glaube dass","word_type":"phrase","level":"B1","unit":"opinions"},
    {"spanish":"pienso que","german":"ich denke dass","word_type":"phrase","level":"B1","unit":"opinions"},
    {"spanish":"por eso","german":"deshalb","word_type":"phrase","level":"B1","unit":"opinions"},
    {"spanish":"sin embargo","german":"jedoch","word_type":"phrase","level":"B1","unit":"opinions","example_sentence":"Sin embargo, hay otra solución.","example_translation":"Es gibt jedoch eine andere Lösung."},
    {"spanish":"el cine","german":"das Kino","word_type":"noun","level":"B1","unit":"culture"},
    {"spanish":"la película","german":"der Film","word_type":"noun","level":"B1","unit":"culture","example_sentence":"¿Has visto esta película?","example_translation":"Hast du diesen Film gesehen?"},
    {"spanish":"el libro","german":"das Buch","word_type":"noun","level":"B1","unit":"culture"},
    {"spanish":"la música","german":"die Musik","word_type":"noun","level":"B1","unit":"culture"},
    {"spanish":"el arte","german":"die Kunst","word_type":"noun","level":"B1","unit":"culture"},
    {"spanish":"aprender","german":"lernen","word_type":"verb","level":"B1","unit":"education","example_sentence":"Estoy aprendiendo español.","example_translation":"Ich lerne Spanisch."},
    {"spanish":"enseñar","german":"lehren / zeigen","word_type":"verb","level":"B1","unit":"education"},
    {"spanish":"el profesor","german":"der Lehrer","word_type":"noun","level":"B1","unit":"education"},
    {"spanish":"la universidad","german":"die Universität","word_type":"noun","level":"B1","unit":"education"},
    {"spanish":"el examen","german":"die Prüfung","word_type":"noun","level":"B1","unit":"education"},
    {"spanish":"aprobado","german":"bestanden","word_type":"adjective","level":"B1","unit":"education"},
    {"spanish":"suspender","german":"durchfallen","word_type":"verb","level":"B1","unit":"education","example_sentence":"He suspendido el examen de matemáticas.","example_translation":"Ich bin durch die Matheprüfung gefallen."},
    {"spanish":"el recuerdo","german":"die Erinnerung","word_type":"noun","level":"B1","unit":"emotions","example_sentence":"Tengo buenos recuerdos de aquel viaje.","example_translation":"Ich habe gute Erinnerungen an jene Reise."},
    {"spanish":"la alegría","german":"die Freude","word_type":"noun","level":"B1","unit":"emotions"},
    {"spanish":"la tristeza","german":"die Traurigkeit","word_type":"noun","level":"B1","unit":"emotions"},
    {"spanish":"el miedo","german":"die Angst","word_type":"noun","level":"B1","unit":"emotions"},
    {"spanish":"la esperanza","german":"die Hoffnung","word_type":"noun","level":"B1","unit":"emotions"},
    {"spanish":"la sorpresa","german":"die Überraschung","word_type":"noun","level":"B1","unit":"emotions"},
    {"spanish":"aunque","german":"obwohl","word_type":"conjunction","level":"B1","unit":"connectors","example_sentence":"Aunque llueva, saldré.","example_translation":"Obwohl es regnet, werde ich ausgehen."},
    {"spanish":"además","german":"außerdem","word_type":"adverb","level":"B1","unit":"connectors"},
    {"spanish":"por lo tanto","german":"daher","word_type":"phrase","level":"B1","unit":"connectors"},
    {"spanish":"mientras","german":"während","word_type":"conjunction","level":"B1","unit":"connectors"},
    {"spanish":"apenas","german":"kaum","word_type":"adverb","level":"B1","unit":"connectors"},
]


_lesson_contents = []

# A0
_lesson_contents.append({
    "type": "dialogue", "intro": "Lerne, dich auf Spanisch vorzustellen.",
    "scenes": [
        {"speaker": "A", "spanish": "Hola! Como te llamas?", "german": "Hallo! Wie heisst du?"},
        {"speaker": "B", "spanish": "Me llamo Maria. Y tu?", "german": "Ich heisse Maria. Und du?"},
        {"speaker": "A", "spanish": "Soy Juan. Mucho gusto.", "german": "Ich bin Juan. Freut mich."},
        {"speaker": "B", "spanish": "El gusto es mio.", "german": "Ganz meinerseits."},
    ],
    "exercise": {"type": "fill_blank", "questions": [
        {"spanish": "Hola, me ____ Ana.", "answer": "llamo", "options": ["llamo", "llamas", "llama"]},
        {"spanish": "Mucho ____.", "answer": "gusto", "options": ["gracias", "gusto", "bueno"]},
    ]},
})

_lesson_contents.append({
    "type": "vocab", "intro": "Lerne die Zahlen von 1 bis 20.",
    "words": [{"spanish": "uno", "german": "eins"}, {"spanish": "dos", "german": "zwei"},
              {"spanish": "tres", "german": "drei"}, {"spanish": "cuatro", "german": "vier"},
              {"spanish": "cinco", "german": "funf"}],
    "exercise": {"type": "match", "pairs": [["uno", "eins"], ["cinco", "funf"], ["diez", "zehn"], ["veinte", "zwanzig"]]},
})

# A1
_lesson_contents.append({
    "type": "dialogue", "intro": "Lerne, wie du in einem spanischen Restaurant bestellst.",
    "scenes": [
        {"speaker": "Camarero", "spanish": "Buenas tardes. Que desea?", "german": "Guten Tag. Was wuenschen Sie?"},
        {"speaker": "Cliente", "spanish": "Quisiera una paella, por favor.", "german": "Ich haette gerne eine Paella, bitte."},
        {"speaker": "Camarero", "spanish": "Y para beber?", "german": "Und zu trinken?"},
        {"speaker": "Cliente", "spanish": "Un vino tinto, gracias.", "german": "Einen Rotwein, danke."},
        {"speaker": "Camarero", "spanish": "Enseguida.", "german": "Kommt sofort."},
    ],
    "exercise": {"type": "fill_blank", "questions": [
        {"spanish": "La ____, por favor.", "answer": "cuenta", "options": ["carta", "cuenta", "comida"]},
        {"spanish": "Quisiera ____ agua.", "answer": "un", "options": ["un", "una", "unos"]},
    ]},
})

_lesson_contents.append({
    "type": "vocab", "intro": "Familienmitglieder auf Spanisch.",
    "words": [{"spanish": "la madre", "german": "die Mutter"}, {"spanish": "el padre", "german": "der Vater"},
              {"spanish": "el hermano", "german": "der Bruder"}, {"spanish": "la hermana", "german": "die Schwester"},
              {"spanish": "el abuelo", "german": "der Grossvater"}, {"spanish": "la abuela", "german": "die Grossmutter"}],
    "exercise": {"type": "multiple_choice", "questions": [
        {"question": "Wie sagt man die Mutter auf Spanisch?", "options": ["la madre", "el padre", "la hermana"], "correct": 0},
    ]},
})

# A2
_lesson_contents.append({
    "type": "dialogue", "intro": "Lerne, nach dem Weg zu fragen und Wegbeschreibungen zu verstehen.",
    "scenes": [
        {"speaker": "Turista", "spanish": "Perdone, donde esta la plaza Mayor?", "german": "Entschuldigung, wo ist die Plaza Mayor?"},
        {"speaker": "Local", "spanish": "Siga todo recto y luego gire a la derecha.", "german": "Gehen Sie geradeaus und biegen Sie dann rechts ab."},
        {"speaker": "Turista", "spanish": "Esta lejos?", "german": "Ist es weit?"},
        {"speaker": "Local", "spanish": "No, esta a cinco minutos andando.", "german": "Nein, es ist fuenf Minuten zu Fuss."},
        {"speaker": "Turista", "spanish": "Muchas gracias.", "german": "Vielen Dank."},
    ],
    "exercise": {"type": "fill_blank", "questions": [
        {"spanish": "Gire a la ____.", "answer": "derecha", "options": ["izquierda", "derecha", "calle"]},
        {"spanish": "Siga ____ recto.", "answer": "todo", "options": ["todo", "toda", "todos"]},
    ]},
})

_lesson_contents.append({
    "type": "dialogue", "intro": "Lerne, ein Hotelzimmer auf Spanisch zu reservieren.",
    "scenes": [
        {"speaker": "Recepcionista", "spanish": "Buenas noches. Tiene reserva?", "german": "Guten Abend. Haben Sie eine Reservierung?"},
        {"speaker": "Cliente", "spanish": "Si, a nombre de Schmidt.", "german": "Ja, auf den Namen Schmidt."},
        {"speaker": "Recepcionista", "spanish": "Aqui esta. Una habitacion doble por tres noches.", "german": "Hier ist sie. Ein Doppelzimmer fuer drei Naechte."},
        {"speaker": "Cliente", "spanish": "A que hora es el desayuno?", "german": "Um wie viel Uhr ist das Fruehstueck?"},
        {"speaker": "Recepcionista", "spanish": "De siete a diez de la manana.", "german": "Von sieben bis zehn Uhr morgens."},
    ],
    "exercise": {"type": "multiple_choice", "questions": [
        {"question": "Was bedeutet habitacion doble?", "options": ["Doppelzimmer", "Einzelzimmer", "Fruehstueck"], "correct": 0},
    ]},
})

# B1
_lesson_contents.append({
    "type": "dialogue", "intro": "Lerne, auf Spanisch ueber aktuelle Themen zu diskutieren.",
    "scenes": [
        {"speaker": "A", "spanish": "Has leido la noticia sobre el cambio climatico?", "german": "Hast du die Nachricht ueber den Klimawandel gelesen?"},
        {"speaker": "B", "spanish": "Si, es muy preocupante. En mi opinion, tenemos que actuar ya.", "german": "Ja, es ist sehr beunruhigend. Meiner Meinung nach muessen wir jetzt handeln."},
        {"speaker": "A", "spanish": "Estoy de acuerdo. Sin embargo, muchos gobiernos no hacen lo suficiente.", "german": "Ich stimme zu. Jedoch tun viele Regierungen nicht genug."},
        {"speaker": "B", "spanish": "Por eso es importante que la gente proteste y exija cambios.", "german": "Deshalb ist es wichtig, dass die Leute protestieren und Veraenderungen fordern."},
    ],
    "exercise": {"type": "fill_blank", "questions": [
        {"spanish": "____ mi opinion, es urgente.", "answer": "En", "options": ["En", "Con", "Por"]},
        {"spanish": "Estoy de ____ contigo.", "answer": "acuerdo", "options": ["acuerdo", "favor", "gusto"]},
    ]},
})

_lesson_contents.append({
    "type": "grammar", "topic": "Preterito Indefinido vs Imperfecto",
    "intro": "Lerne den Unterschied zwischen den beiden Vergangenheitsformen.",
    "explanation": "Indefinido: abgeschlossene Handlungen. Imperfecto: Gewohnheiten, Beschreibungen, Hintergrund.",
    "examples": [
        {"spanish": "Ayer fui al cine.", "german": "Gestern ging ich ins Kino.", "tense": "indefinido"},
        {"spanish": "Cuando era nino, iba al cine cada semana.", "german": "Als ich Kind war, ging ich jede Woche ins Kino.", "tense": "imperfecto"},
    ],
    "exercise": {"type": "fill_blank", "questions": [
        {"spanish": "Ayer ____ (comer) paella.", "answer": "comi"},
        {"spanish": "De nino, siempre ____ (jugar) al futbol.", "answer": "jugaba"},
    ]},
})

import json as _json

LESSONS = [
    {"title": "Sich vorstellen", "level": "A0", "unit": "greetings", "lesson_type": "dialogue",
     "sort_order": 1, "content_json": _json.dumps(_lesson_contents[0], ensure_ascii=False)},
    {"title": "Erste Zahlen", "level": "A0", "unit": "numbers", "lesson_type": "vocab",
     "sort_order": 2, "content_json": _json.dumps(_lesson_contents[1], ensure_ascii=False)},
    {"title": "Im Restaurant bestellen", "level": "A1", "unit": "restaurant", "lesson_type": "dialogue",
     "sort_order": 3, "content_json": _json.dumps(_lesson_contents[2], ensure_ascii=False)},
    {"title": "Die Familie", "level": "A1", "unit": "family", "lesson_type": "vocab",
     "sort_order": 4, "content_json": _json.dumps(_lesson_contents[3], ensure_ascii=False)},
    {"title": "Nach dem Weg fragen", "level": "A2", "unit": "directions", "lesson_type": "dialogue",
     "sort_order": 5, "content_json": _json.dumps(_lesson_contents[4], ensure_ascii=False)},
    {"title": "Ein Hotelzimmer buchen", "level": "A2", "unit": "travel", "lesson_type": "dialogue",
     "sort_order": 6, "content_json": _json.dumps(_lesson_contents[5], ensure_ascii=False)},
    {"title": "Ueber Nachrichten sprechen", "level": "B1", "unit": "news", "lesson_type": "dialogue",
     "sort_order": 7, "content_json": _json.dumps(_lesson_contents[6], ensure_ascii=False)},
    {"title": "Ueber Vergangenes erzaehlen", "level": "B1", "unit": "culture", "lesson_type": "grammar",
     "sort_order": 8, "content_json": _json.dumps(_lesson_contents[7], ensure_ascii=False)},
]


PLACEMENT_QUESTIONS = [
    {"spanish":"¿Cómo te llamas?",
     "options":["a) Me llamo bien, gracias", "b) Me llamo Juan", "c) Me llamo en Madrid", "d) Llamo por teléfono"],
     "correct_index":1, "level_hint":"A0"},

    {"spanish":"¿De dónde eres?",
     "options":["a) Soy de Alemania", "b) Soy alemán", "c) Tengo 30 años", "d) Estoy bien"],
     "correct_index":0, "level_hint":"A0"},

    {"spanish":"¿Cuántos años tienes?",
     "options":["a) Soy 30 años", "b) Estoy 30", "c) Tengo 30 años", "d) Hago 30 años"],
     "correct_index":2, "level_hint":"A1"},

    {"spanish":"Elige la frase correcta:",
     "options":["a) El coche de Juan es rojo", "b) El coche de Juan está rojo", "c) El coche de Juan son rojo", "d) El coche de Juan rojo es"],
     "correct_index":0, "level_hint":"A1"},

    {"spanish":"Completa: Ayer ___ al cine con mis amigos.",
     "options":["a) voy", "b) fui", "c) iba", "d) iré"],
     "correct_index":1, "level_hint":"A2"},

    {"spanish":"Completa: Cuando era niño, ___ en un pueblo pequeño.",
     "options":["a) viví", "b) vivo", "c) vivía", "d) viviré"],
     "correct_index":2, "level_hint":"A2"},

    {"spanish":"Elige la frase correcta:",
     "options":["a) Me gusta los perros", "b) Me gustan los perros", "c) Me gusto los perros", "d) Yo gusto los perros"],
     "correct_index":1, "level_hint":"A2"},

    {"spanish":"Completa: Quiero que tú ___ a la fiesta.",
     "options":["a) vienes", "b) vengas", "c) vendrás", "d) viniste"],
     "correct_index":1, "level_hint":"B1"},

    {"spanish":"Completa: Si tuviera dinero, ___ un coche nuevo.",
     "options":["a) compro", "b) compraría", "c) compré", "d) compraba"],
     "correct_index":1, "level_hint":"B1"},

    {"spanish":"Elige la frase correcta (indirekte Rede):",
     "options":["a) Dijo que vendrá mañana", "b) Dijo que vendría mañana", "c) Dijo que viene mañana", "d) Dijo que ha venido mañana"],
     "correct_index":1, "level_hint":"B1"},
]
