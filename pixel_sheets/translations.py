"""Etsy translations (title, tags, description) for the Christmas Math Mystery Pictures listing.

    python translations.py check            # validate only
    python translations.py upload [lang..]  # create/update on Etsy

The product files are in English; every description says so.
"""
import json
import re
import sys
from pathlib import Path

import make_listing as L

LISTING_ID = json.loads((L.OUT / "uploaded.json").read_text())["listing_id"]
TAG_OK = re.compile(r"^[\w \-']+$")

T = {}

T["fr"] = dict(
    title="Maths de Noël Images Mystères, 40 Activités Pixel Art Autocorrectives, Google Sheets, Multiplication Division Addition Soustraction",
    tags=["image mystère maths", "pixel art maths", "maths google sheets", "maths de noël", "jeu multiplication",
          "exercices division", "calcul addition", "autocorrectif", "google classroom", "ressource enseignant",
          "atelier maths", "activité de noël", "soustraction"],
    description="""Soyez l'enseignant(e) dont ils se souviendront à Noël !

Changez la façon dont votre classe s'entraîne en maths. Au lieu d'une fiche de plus, donnez-leur un mystère à résoudre : chaque bonne réponse dévoile une partie d'une image de Noël en pixel art cachée. Les élèves continuent, vérifient eux-mêmes leur travail et en redemandent !

★ POURQUOI LES ENSEIGNANTS L'ADORENT
• Aucune correction : la feuille vérifie chaque réponse pour vous
• Tous les élèves sont motivés, des plus fragiles aux plus rapides
• Retour immédiat : les erreurs sont corrigées tout de suite
• Zéro préparation : faites une copie, distribuez, c'est prêt

★ COMMENT ÇA MARCHE
• L'élève tape la réponse dans la case jaune et appuie sur Entrée
• ✓ vert = juste, et une partie de l'image apparaît
• ✗ rouge = réessayer. Rien n'apparaît tant que la réponse n'est pas juste
• Un score en direct indique la progression : "Correct: 14 / 20"

★ CONTENU
• Multiplication : 10 images, tables de 2 à 12
• Division : 10 images, jusqu'à 144 ÷ 12
• Addition : 10 images, nombres à 2 chiffres, résultats jusqu'à 99
• Soustraction : 10 images, nombres à 2 chiffres, sans résultat négatif
• Guide enseignant de 24 pages avec liens Google Sheets, instructions et corrigés avec chaque image terminée
• 20 questions par image, 800 questions au total

★ LES 10 IMAGES MYSTÈRES
Sapin, bonhomme de neige, cadeau, bonhomme en pain d'épices, bonnet de Père Noël, renne, sucre d'orge, chaussette, boule de Noël et chocolat chaud. Les onglets s'appellent Picture 1 à Picture 10 pour garder le secret.

★ UTILISATION
1. Téléchargez les fichiers et ouvrez le guide (PDF)
2. Cliquez sur le lien Google Sheets d'une compétence puis "Créer une copie"
3. Dans Google Classroom, joignez votre copie avec "Créer une copie pour chaque élève"
Vous préférez Excel ? Les fichiers .xlsx fonctionnent de la même façon.

★ BON À SAVOIR
• Les activités et le guide sont en ANGLAIS (les nombres et les symboles mathématiques sont universels)
• Produit NUMÉRIQUE, rien ne sera expédié
• Il faut un compte Google gratuit (Google Sheets) ou Microsoft Excel
• Fonctionne sur Chromebook, ordinateur portable et de bureau, sans extension
• Idéal pour 7 à 10 ans (CE1 à CM1)
• Pixel art et puzzles créés par notre boutique avec des outils numériques et assistés par IA

★ CONDITIONS D'UTILISATION
Pour un(e) enseignant(e) dans sa propre classe. Merci de ne pas partager, revendre ou publier les fichiers ou les liens.""")

T["de"] = dict(
    title="Weihnachts-Mathe Rätselbilder, 40 Selbstkontrollierende Pixel Art Aufgaben, Google Sheets, Einmaleins Division Plus Minus",
    tags=["mathe rätselbild", "pixel art mathe", "google sheets mathe", "weihnachten mathe", "einmaleins üben",
          "division üben", "plus und minus", "selbstkontrolle", "google classroom", "lehrer material",
          "mathe grundschule", "mathe stationen", "weihnachtsaktivität"],
    description="""Sei die Lehrkraft, an die sich deine Klasse erinnert!

Verändere, wie deine Klasse Mathe übt. Statt eines weiteren Arbeitsblatts bekommen die Kinder ein Rätsel: Jede richtige Antwort deckt einen Teil eines versteckten Weihnachtsbildes in Pixel Art auf. So bleiben sie dran, kontrollieren sich selbst und wollen "nur noch eine Aufgabe"!

★ WARUM LEHRKRÄFTE ES LIEBEN
• Keine Korrektur: Die Tabelle prüft jede Antwort für dich
• Alle Kinder machen mit, von schwächeren bis zu schnellen Rechnern
• Sofortiges Feedback: Fehler werden gleich verbessert
• Keine Vorbereitung: Kopie erstellen, zuweisen, fertig

★ SO FUNKTIONIERT ES
• Die Antwort ins gelbe Feld tippen und Enter drücken
• Grünes ✓ = richtig, ein Teil des Bildes erscheint
• Rotes ✗ = nochmal versuchen. Es wird nichts aufgedeckt, bis die Antwort stimmt
• Ein Live-Punktestand zeigt den Fortschritt: "Correct: 14 / 20"

★ INHALT
• Einmaleins: 10 Bilder, Reihen 2 bis 12
• Division: 10 Bilder, bis 144 ÷ 12
• Addition: 10 Bilder, zweistellige Zahlen, Ergebnisse bis 99
• Subtraktion: 10 Bilder, zweistellige Zahlen, keine negativen Ergebnisse
• 24-seitiger Lehrerleitfaden mit Google-Sheets-Links, Anleitung und Lösungen mit jedem fertigen Bild
• 20 Aufgaben pro Bild, insgesamt 800 Aufgaben

★ DIE 10 RÄTSELBILDER
Weihnachtsbaum, Schneemann, Geschenk, Lebkuchenmann, Weihnachtsmütze, Rentier, Zuckerstange, Nikolausstiefel, Christbaumkugel und heiße Schokolade. Die Tabellenblätter heißen Picture 1 bis Picture 10, damit das Bild ein Geheimnis bleibt.

★ ANWENDUNG
1. Dateien herunterladen und den Leitfaden (PDF) öffnen
2. Den Google-Sheets-Link einer Rechenart anklicken und "Kopie erstellen" wählen
3. In Google Classroom die Kopie anhängen und "Kopie für jeden Schüler erstellen" wählen
Lieber Excel? Die .xlsx-Dateien funktionieren genauso.

★ GUT ZU WISSEN
• Aufgaben und Leitfaden sind auf ENGLISCH (Zahlen und Rechenzeichen sind international)
• DIGITALER DOWNLOAD, es wird nichts verschickt
• Benötigt ein kostenloses Google-Konto (Google Sheets) oder Microsoft Excel
• Läuft auf Chromebooks, Laptops und PCs, ohne Add-ons
• Ideal für 7 bis 10 Jahre (Klasse 2 bis 4)
• Pixel Art und Rätsel wurden von unserem Shop mit digitalen und KI-gestützten Werkzeugen erstellt

★ NUTZUNGSBEDINGUNGEN
Für eine Lehrkraft in der eigenen Klasse. Bitte Dateien und Links nicht weitergeben, weiterverkaufen oder öffentlich posten.""")

T["es"] = dict(
    title="Matemáticas Navideñas Imágenes Misterio, 40 Actividades Pixel Art Autocorregibles, Google Sheets, Multiplicación División Suma Resta",
    tags=["imagen misteriosa", "pixel art matemática", "google sheets mates", "matemáticas navidad", "multiplicación",
          "práctica división", "sumas y restas", "autocorregible", "google classroom", "recursos docentes",
          "matemáticas primaria", "rincón matemático", "actividad navideña"],
    description="""¡Sé el maestro o la maestra que recordarán esta Navidad!

Cambia la forma en que tu clase practica matemáticas. En lugar de otra ficha, dales un misterio que resolver: cada respuesta correcta revela parte de una imagen navideña oculta en pixel art. Siguen adelante, revisan su propio trabajo y piden "¡solo una más!"

★ POR QUÉ LES ENCANTA A LOS DOCENTES
• Sin corregir: la hoja revisa cada respuesta por ti
• Todos los alumnos participan, desde los que necesitan apoyo hasta los más rápidos
• Retroalimentación inmediata: los errores se corrigen al momento
• Cero preparación: haz una copia, asígnala y listo

★ CÓMO FUNCIONA
• El alumno escribe la respuesta en la casilla amarilla y pulsa Intro
• ✓ verde = correcto, y aparece parte de la imagen
• ✗ rojo = inténtalo de nuevo. No se revela nada hasta que la respuesta es correcta
• Una puntuación en vivo muestra el progreso: "Correct: 14 / 20"

★ QUÉ INCLUYE
• Multiplicación: 10 imágenes, tablas del 2 al 12
• División: 10 imágenes, hasta 144 ÷ 12
• Suma: 10 imágenes, números de 2 cifras, resultados hasta 99
• Resta: 10 imágenes, números de 2 cifras, sin resultados negativos
• Guía docente de 24 páginas con enlaces de Google Sheets, instrucciones y solucionario con cada imagen terminada
• 20 preguntas por imagen, 800 en total

★ LAS 10 IMÁGENES MISTERIOSAS
Árbol de Navidad, muñeco de nieve, regalo, hombre de jengibre, gorro de Papá Noel, reno, bastón de caramelo, calcetín navideño, bola de Navidad y chocolate caliente. Las pestañas se llaman Picture 1 a Picture 10 para mantener el secreto.

★ CÓMO USARLO
1. Descarga los archivos y abre la guía (PDF)
2. Haz clic en el enlace de Google Sheets de una operación y elige "Hacer una copia"
3. En Google Classroom, adjunta tu copia con "Hacer una copia para cada alumno"
¿Prefieres Excel? Los archivos .xlsx funcionan igual.

★ IMPORTANTE
• Las actividades y la guía están en INGLÉS (los números y símbolos matemáticos son universales)
• DESCARGA DIGITAL, no se envía nada físico
• Necesitas una cuenta gratuita de Google (Google Sheets) o Microsoft Excel
• Funciona en Chromebooks, portátiles y ordenadores, sin complementos
• Ideal para 7 a 10 años (2.º a 4.º de primaria)
• El pixel art y los ejercicios fueron creados por nuestra tienda con herramientas digitales y asistidas por IA

★ CONDICIONES DE USO
Para un docente en su propia clase. Por favor, no compartas, revendas ni publiques los archivos o enlaces.""")

T["it"] = dict(
    title="Matematica di Natale Immagini Misteriose, 40 Attività Pixel Art Autocorrettive, Google Sheets, Tabelline Divisioni Addizioni",
    tags=["immagine misteriosa", "pixel art matematica", "google sheets", "matematica natale", "tabelline",
          "divisioni", "addizioni", "sottrazioni", "autocorrettivo", "google classroom", "risorse insegnanti",
          "matematica primaria", "attività natalizia"],
    description="""Sii l'insegnante che ricorderanno questo Natale!

Cambia il modo in cui la tua classe si esercita in matematica. Invece dell'ennesima scheda, dai loro un mistero da risolvere: ogni risposta corretta svela una parte di un'immagine natalizia nascosta in pixel art. Continuano, si autocorreggono e chiedono "ancora una!"

★ PERCHÉ PIACE AGLI INSEGNANTI
• Niente correzioni: il foglio controlla ogni risposta per te
• Tutti coinvolti, da chi fa fatica a chi finisce presto
• Feedback immediato: gli errori si correggono subito
• Zero preparazione: crea una copia, assegnala ed è fatta

★ COME FUNZIONA
• Lo studente scrive la risposta nella casella gialla e preme Invio
• ✓ verde = giusto, e appare una parte dell'immagine
• ✗ rosso = riprova. Non si svela nulla finché la risposta non è giusta
• Un punteggio in tempo reale mostra i progressi: "Correct: 14 / 20"

★ COSA È INCLUSO
• Moltiplicazioni: 10 immagini, tabelline dal 2 al 12
• Divisioni: 10 immagini, fino a 144 ÷ 12
• Addizioni: 10 immagini, numeri a 2 cifre, risultati fino a 99
• Sottrazioni: 10 immagini, numeri a 2 cifre, nessun risultato negativo
• Guida per l'insegnante di 24 pagine con link Google Sheets, istruzioni e soluzioni con ogni immagine completata
• 20 domande per immagine, 800 in totale

★ LE 10 IMMAGINI MISTERIOSE
Albero di Natale, pupazzo di neve, regalo, omino di pan di zenzero, cappello di Babbo Natale, renna, bastoncino di zucchero, calza della Befana, pallina di Natale e cioccolata calda. Le schede si chiamano Picture 1 a Picture 10, così l'immagine resta un segreto.

★ COME USARLO
1. Scarica i file e apri la guida (PDF)
2. Clicca sul link Google Sheets di un'operazione e scegli "Crea una copia"
3. In Google Classroom allega la copia con "Crea una copia per ogni studente"
Preferisci Excel? I file .xlsx funzionano allo stesso modo.

★ DA SAPERE
• Le attività e la guida sono in INGLESE (numeri e simboli matematici sono universali)
• DOWNLOAD DIGITALE, non verrà spedito nulla
• Serve un account Google gratuito (Google Sheets) o Microsoft Excel
• Funziona su Chromebook, portatili e computer fissi, senza componenti aggiuntivi
• Ideale per 7-10 anni (classi 2ª-4ª primaria)
• Pixel art e esercizi creati dal nostro negozio con strumenti digitali e assistiti dall'IA

★ CONDIZIONI D'USO
Per un insegnante nella propria classe. Per favore non condividere, rivendere o pubblicare i file o i link.""")

T["nl"] = dict(
    title="Kerst Rekenen Mysterieplaatjes, 40 Zelfcorrigerende Pixel Art Opdrachten, Google Sheets, Vermenigvuldigen Delen Optellen Aftrekken",
    tags=["rekenen mysterie", "pixel art rekenen", "google sheets", "kerst rekenen", "tafels oefenen",
          "delen oefenen", "optellen aftrekken", "zelfcorrigerend", "google classroom", "lesmateriaal",
          "rekenen groep 5", "rekenhoek", "kerstactiviteit"],
    description="""Wees de leerkracht die ze zich herinneren deze kerst!

Verander de manier waarop je klas rekenen oefent. In plaats van nog een werkblad krijgen ze een mysterie: elk goed antwoord onthult een deel van een verborgen kerstplaatje in pixel art. Ze blijven doorgaan, controleren zichzelf en vragen om "nog eentje!"

★ WAAROM LEERKRACHTEN HET GEWELDIG VINDEN
• Niet nakijken: het blad controleert elk antwoord voor je
• Elke leerling doet mee, van zwakkere rekenaars tot snelle werkers
• Directe feedback: fouten worden meteen verbeterd
• Geen voorbereiding: kopie maken, uitdelen, klaar

★ ZO WERKT HET
• De leerling typt het antwoord in het gele vak en drukt op Enter
• Groen ✓ = goed, en een deel van het plaatje verschijnt
• Rood ✗ = probeer opnieuw. Er verschijnt niets tot het antwoord goed is
• Een live score toont de voortgang: "Correct: 14 / 20"

★ INHOUD
• Vermenigvuldigen: 10 plaatjes, tafels van 2 t/m 12
• Delen: 10 plaatjes, tot 144 ÷ 12
• Optellen: 10 plaatjes, getallen van 2 cijfers, uitkomsten tot 99
• Aftrekken: 10 plaatjes, getallen van 2 cijfers, geen negatieve uitkomsten
• Lerarenhandleiding van 24 pagina's met Google Sheets-links, uitleg en antwoordbladen met elk af plaatje
• 20 vragen per plaatje, 800 in totaal

★ DE 10 MYSTERIEPLAATJES
Kerstboom, sneeuwpop, cadeau, peperkoekmannetje, kerstmuts, rendier, zuurstok, kerstsok, kerstbal en warme chocolademelk. De tabbladen heten Picture 1 t/m Picture 10, zodat het plaatje geheim blijft.

★ GEBRUIK
1. Download de bestanden en open de handleiding (PDF)
2. Klik op de Google Sheets-link van een onderdeel en kies "Een kopie maken"
3. Voeg je kopie in Google Classroom toe met "Een kopie maken voor elke leerling"
Liever Excel? De .xlsx-bestanden werken op dezelfde manier.

★ GOED OM TE WETEN
• De opdrachten en handleiding zijn in het ENGELS (getallen en rekentekens zijn universeel)
• DIGITALE DOWNLOAD, er wordt niets verzonden
• Je hebt een gratis Google-account (Google Sheets) of Microsoft Excel nodig
• Werkt op Chromebooks, laptops en computers, zonder extensies
• Ideaal voor 7 tot 10 jaar (groep 4 t/m 6)
• Pixel art en opdrachten zijn door onze winkel gemaakt met digitale en AI-ondersteunde hulpmiddelen

★ GEBRUIKSVOORWAARDEN
Voor één leerkracht in de eigen klas. Deel, verkoop of publiceer de bestanden of links niet.""")

T["pt"] = dict(
    title="Matemática de Natal Imagens Misteriosas, 40 Atividades Pixel Art Autocorretivas, Google Sheets, Multiplicação Divisão Adição Subtração",
    tags=["imagem misteriosa", "pixel art matemática", "google sheets", "matemática natal", "tabuada",
          "praticar divisão", "adição e subtração", "autocorretivo", "google classroom", "recursos professor",
          "matemática primária", "atividade de natal", "multiplicação"],
    description="""Seja o professor ou a professora que eles vão lembrar neste Natal!

Mude a forma como a sua turma pratica matemática. Em vez de mais uma ficha, dê a eles um mistério para resolver: cada resposta certa revela parte de uma imagem de Natal escondida em pixel art. Eles continuam, conferem o próprio trabalho e pedem "só mais uma!"

★ POR QUE OS PROFESSORES ADORAM
• Sem correção: a planilha confere cada resposta por você
• Todos os alunos participam, dos que têm dificuldade aos mais rápidos
• Feedback imediato: os erros são corrigidos na hora
• Zero preparação: faça uma cópia, atribua e pronto

★ COMO FUNCIONA
• O aluno digita a resposta na caixa amarela e aperta Enter
• ✓ verde = certo, e parte da imagem aparece
• ✗ vermelho = tente de novo. Nada é revelado até a resposta estar certa
• Uma pontuação ao vivo mostra o progresso: "Correct: 14 / 20"

★ O QUE ESTÁ INCLUÍDO
• Multiplicação: 10 imagens, tabuada do 2 ao 12
• Divisão: 10 imagens, até 144 ÷ 12
• Adição: 10 imagens, números de 2 algarismos, resultados até 99
• Subtração: 10 imagens, números de 2 algarismos, sem resultados negativos
• Guia do professor de 24 páginas com links do Google Sheets, instruções e gabaritos com cada imagem pronta
• 20 questões por imagem, 800 no total

★ AS 10 IMAGENS MISTERIOSAS
Árvore de Natal, boneco de neve, presente, homem de gengibre, gorro de Papai Noel, rena, bengala doce, meia de Natal, bola de Natal e chocolate quente. As abas se chamam Picture 1 a Picture 10 para manter o segredo.

★ COMO USAR
1. Baixe os arquivos e abra o guia (PDF)
2. Clique no link do Google Sheets de uma operação e escolha "Fazer uma cópia"
3. No Google Classroom, anexe sua cópia com "Fazer uma cópia para cada aluno"
Prefere Excel? Os arquivos .xlsx funcionam do mesmo jeito.

★ BOM SABER
• As atividades e o guia estão em INGLÊS (números e símbolos matemáticos são universais)
• DOWNLOAD DIGITAL, nada será enviado pelo correio
• É preciso uma conta Google gratuita (Google Sheets) ou o Microsoft Excel
• Funciona em Chromebooks, notebooks e computadores, sem extensões
• Ideal para 7 a 10 anos (2º ao 4º ano)
• Pixel art e exercícios criados pela nossa loja com ferramentas digitais e assistidas por IA

★ TERMOS DE USO
Para um professor na sua própria turma. Por favor, não compartilhe, revenda nem publique os arquivos ou links.""")

T["pl"] = dict(
    title="Świąteczna Matematyka Tajemnicze Obrazki, 40 Zadań Pixel Art z Samosprawdzaniem, Google Sheets, Mnożenie Dzielenie Dodawanie",
    tags=["tajemniczy obrazek", "pixel art matematyka", "google sheets", "matematyka święta", "tabliczka mnożenia",
          "dzielenie", "dodawanie", "odejmowanie", "samosprawdzanie", "google classroom", "materiały nauczyciel",
          "zadania świąteczne", "matematyka szkoła"],
    description="""Bądź nauczycielem, którego zapamiętają w te święta!

Zmień sposób, w jaki Twoja klasa ćwiczy matematykę. Zamiast kolejnej karty pracy daj uczniom zagadkę: każda poprawna odpowiedź odkrywa fragment ukrytego świątecznego obrazka pixel art. Uczniowie chcą rozwiązywać dalej, sami sprawdzają swoją pracę i proszą o "jeszcze jedno!"

★ DLACZEGO NAUCZYCIELE TO KOCHAJĄ
• Bez sprawdzania: arkusz sprawdza każdą odpowiedź za Ciebie
• Wszyscy uczniowie zaangażowani, od słabszych po najszybszych
• Natychmiastowa informacja zwrotna: błędy są od razu poprawiane
• Zero przygotowań: utwórz kopię, przydziel i gotowe

★ JAK TO DZIAŁA
• Uczeń wpisuje odpowiedź w żółte pole i naciska Enter
• Zielony ✓ = dobrze, pojawia się fragment obrazka
• Czerwony ✗ = spróbuj ponownie. Nic się nie odkrywa, dopóki odpowiedź nie jest poprawna
• Wynik na żywo pokazuje postęp: "Correct: 14 / 20"

★ CO ZAWIERA
• Mnożenie: 10 obrazków, tabliczka od 2 do 12
• Dzielenie: 10 obrazków, do 144 ÷ 12
• Dodawanie: 10 obrazków, liczby dwucyfrowe, wyniki do 99
• Odejmowanie: 10 obrazków, liczby dwucyfrowe, bez wyników ujemnych
• 24-stronicowy przewodnik dla nauczyciela z linkami Google Sheets, instrukcją i odpowiedziami z każdym gotowym obrazkiem
• 20 pytań na obrazek, razem 800 pytań

★ 10 TAJEMNICZYCH OBRAZKÓW
Choinka, bałwan, prezent, piernikowy ludzik, czapka Mikołaja, renifer, cukrowa laska, świąteczna skarpeta, bombka i gorąca czekolada. Karty nazywają się Picture 1 do Picture 10, więc obrazek pozostaje tajemnicą.

★ JAK UŻYWAĆ
1. Pobierz pliki i otwórz przewodnik (PDF)
2. Kliknij link Google Sheets dla wybranego działania i wybierz "Utwórz kopię"
3. W Google Classroom dołącz kopię z opcją "Utwórz kopię dla każdego ucznia"
Wolisz Excel? Pliki .xlsx działają tak samo.

★ WARTO WIEDZIEĆ
• Zadania i przewodnik są w języku ANGIELSKIM (liczby i znaki matematyczne są uniwersalne)
• PRODUKT CYFROWY, nic nie zostanie wysłane
• Potrzebne jest darmowe konto Google (Google Sheets) lub Microsoft Excel
• Działa na Chromebookach, laptopach i komputerach, bez dodatków
• Idealne dla dzieci w wieku 7-10 lat (klasy 1-4)
• Pixel art i zadania zostały stworzone przez nasz sklep przy pomocy narzędzi cyfrowych i AI

★ WARUNKI KORZYSTANIA
Dla jednego nauczyciela we własnej klasie. Prosimy nie udostępniać, nie odsprzedawać i nie publikować plików ani linków.""")

T["ru"] = dict(
    title="Рождественская математика картинки-загадки, 40 заданий пиксель-арт с самопроверкой, Google Sheets, умножение деление сложение",
    tags=["картинка загадка", "пиксель арт", "google sheets", "математика", "таблица умножения", "деление",
          "сложение", "вычитание", "самопроверка", "google classroom", "для учителя", "начальная школа", "рождество"],
    description="""Станьте учителем, которого запомнят в это Рождество!

Измените то, как ваш класс тренируется в математике. Вместо очередного листа с примерами дайте детям загадку: каждый правильный ответ открывает часть скрытой рождественской картинки в стиле пиксель-арт. Дети не останавливаются, сами проверяют себя и просят "ещё один!"

★ ПОЧЕМУ УЧИТЕЛЯ ЭТО ЛЮБЯТ
• Не нужно проверять: таблица проверяет каждый ответ за вас
• Вовлечены все ученики, от отстающих до самых быстрых
• Мгновенная обратная связь: ошибки исправляются сразу
• Никакой подготовки: создайте копию, раздайте, готово

★ КАК ЭТО РАБОТАЕТ
• Ученик вводит ответ в жёлтую ячейку и нажимает Enter
• Зелёная ✓ = верно, и появляется часть картинки
• Красный ✗ = попробуй ещё раз. Ничего не открывается, пока ответ неверный
• Счёт в реальном времени показывает прогресс: "Correct: 14 / 20"

★ ЧТО ВХОДИТ
• Умножение: 10 картинок, таблица от 2 до 12
• Деление: 10 картинок, до 144 ÷ 12
• Сложение: 10 картинок, двузначные числа, ответы до 99
• Вычитание: 10 картинок, двузначные числа, без отрицательных ответов
• Руководство для учителя на 24 страницы со ссылками Google Sheets, инструкцией и ответами с каждой готовой картинкой
• 20 вопросов на картинку, всего 800

★ 10 КАРТИНОК-ЗАГАДОК
Ёлка, снеговик, подарок, пряничный человечек, шапка Санты, олень, леденцовая трость, рождественский носок, ёлочный шар и горячий шоколад. Листы называются Picture 1 - Picture 10, чтобы картинка оставалась секретом.

★ КАК ПОЛЬЗОВАТЬСЯ
1. Скачайте файлы и откройте руководство (PDF)
2. Нажмите ссылку Google Sheets для нужного действия и выберите "Создать копию"
3. В Google Classroom прикрепите копию с вариантом "Создать копию для каждого учащегося"
Предпочитаете Excel? Файлы .xlsx работают так же.

★ ВАЖНО
• Задания и руководство на АНГЛИЙСКОМ языке (числа и математические знаки универсальны)
• ЦИФРОВОЙ ТОВАР, ничего не отправляется по почте
• Нужен бесплатный аккаунт Google (Google Sheets) или Microsoft Excel
• Работает на Chromebook, ноутбуках и компьютерах, без расширений
• Подходит для детей 7-10 лет (1-4 класс)
• Пиксель-арт и задания созданы нашим магазином с помощью цифровых инструментов и ИИ

★ УСЛОВИЯ ИСПОЛЬЗОВАНИЯ
Для одного учителя в своём классе. Пожалуйста, не передавайте, не перепродавайте и не публикуйте файлы и ссылки.""")

T["sv"] = dict(
    title="Jul Matte Mysteriebilder, 40 Självrättande Pixel Art Uppgifter, Google Sheets, Multiplikation Division Addition Subtraktion",
    tags=["mysteriebild matte", "pixel art matte", "google sheets", "julmatte", "multiplikation", "division",
          "addition", "subtraktion", "självrättande", "google classroom", "lärarmaterial", "matte lågstadiet",
          "julaktivitet"],
    description="""Bli läraren de minns i jul!

Förändra hur din klass tränar matte. I stället för ännu ett arbetsblad får eleverna ett mysterium att lösa: varje rätt svar avslöjar en del av en dold julbild i pixel art. De fortsätter, rättar sig själva och ber om "bara en till!"

★ DÄRFÖR ÄLSKAR LÄRARE DET
• Ingen rättning: arket kontrollerar varje svar åt dig
• Alla elever engagerade, från de som behöver stöd till de snabbaste
• Direkt återkoppling: fel rättas på en gång
• Ingen förberedelse: gör en kopia, dela ut, klart

★ SÅ FUNGERAR DET
• Eleven skriver svaret i den gula rutan och trycker Enter
• Grön ✓ = rätt, och en del av bilden visas
• Rött ✗ = försök igen. Inget visas förrän svaret är rätt
• En poängräknare visar framstegen: "Correct: 14 / 20"

★ DETTA INGÅR
• Multiplikation: 10 bilder, tabellerna 2 till 12
• Division: 10 bilder, upp till 144 ÷ 12
• Addition: 10 bilder, tvåsiffriga tal, svar upp till 99
• Subtraktion: 10 bilder, tvåsiffriga tal, inga negativa svar
• Lärarhandledning på 24 sidor med Google Sheets-länkar, instruktioner och facit med varje färdig bild
• 20 frågor per bild, 800 totalt

★ DE 10 MYSTERIEBILDERNA
Julgran, snögubbe, paket, pepparkaksgubbe, tomteluva, ren, polkagrisstång, julstrumpa, julgranskula och varm choklad. Flikarna heter Picture 1 till Picture 10 så att bilden förblir en hemlighet.

★ SÅ ANVÄNDER DU DET
1. Ladda ner filerna och öppna handledningen (PDF)
2. Klicka på Google Sheets-länken för ett räknesätt och välj "Gör en kopia"
3. Bifoga kopian i Google Classroom med "Gör en kopia för varje elev"
Föredrar du Excel? .xlsx-filerna fungerar på samma sätt.

★ BRA ATT VETA
• Uppgifterna och handledningen är på ENGELSKA (siffror och räknetecken är universella)
• DIGITAL NEDLADDNING, inget skickas hem
• Du behöver ett gratis Google-konto (Google Sheets) eller Microsoft Excel
• Fungerar på Chromebooks, bärbara och stationära datorer, utan tillägg
• Passar 7-10 år (åk 1-4)
• Pixel art och uppgifter är skapade av vår butik med digitala och AI-stödda verktyg

★ ANVÄNDARVILLKOR
För en lärare i den egna klassen. Dela, sälj vidare eller publicera inte filerna eller länkarna.""")

T["ja"] = dict(
    title="クリスマス算数 ミステリーピクチャー 自動採点 ピクセルアート40問題 Googleスプレッドシート 掛け算 割り算 足し算 引き算",
    tags=["ミステリーピクチャー", "ピクセルアート", "google sheets", "クリスマス算数", "掛け算", "割り算", "足し算",
          "引き算", "自動採点", "google classroom", "教材", "小学生算数", "クリスマス学習"],
    description="""このクリスマス、子どもたちの記憶に残る先生になりましょう！

算数の練習の仕方を変えてみませんか。いつものプリントの代わりに、謎解きを。正解するたびに、隠れたクリスマスのピクセルアートが少しずつ現れます。子どもたちは夢中で解き進め、自分で答えを確かめ、「もう1問！」とせがみます。

★ 先生に喜ばれる理由
• 採点不要：シートがすべての答えを自動でチェック
• 苦手な子も早く終わる子も、みんなが夢中に
• すぐにフィードバック：間違いはその場で直せます
• 準備ゼロ：コピーを作って配るだけ

★ 使い方のしくみ
• 黄色のマスに答えを入力してEnter
• 緑の✓＝正解、絵の一部が現れます
• 赤の✗＝もう一度。正解するまで何も現れません
• リアルタイムのスコア表示：「Correct: 14 / 20」

★ 内容
• 掛け算：10枚、2の段から12の段
• 割り算：10枚、144 ÷ 12まで
• 足し算：10枚、2けたの数、答えは99まで
• 引き算：10枚、2けたの数、答えはマイナスなし
• 24ページの先生用ガイド（Googleスプレッドシートのリンク、使い方、完成図つき解答）
• 1枚につき20問、合計800問

★ 10枚のミステリーピクチャー
クリスマスツリー、雪だるま、プレゼント、ジンジャーブレッドマン、サンタ帽、トナカイ、キャンディケイン、靴下、オーナメント、ホットココア。シート名は Picture 1〜Picture 10 なので、絵は完成まで秘密です。

★ ご利用方法
1. ファイルをダウンロードし、ガイド（PDF）を開く
2. 計算の種類ごとのGoogleスプレッドシートのリンクをクリックし「コピーを作成」
3. Google Classroomでコピーを添付し「各生徒にコピーを作成」を選択
Excel派の方は .xlsx ファイルでも同じように使えます。

★ ご注意
• 問題とガイドは英語です（数字と計算記号は世界共通です）
• デジタルダウンロード商品です。商品の発送はありません
• 無料のGoogleアカウント（Googleスプレッドシート）またはMicrosoft Excelが必要です
• Chromebook、ノートパソコン、デスクトップで動作。アドオン不要
• 7〜10歳（小学1〜4年生）向け
• ピクセルアートと問題は、デジタルツールとAI支援ツールを使って当店が作成しました

★ 利用規約
1名の先生がご自身のクラスでご利用いただけます。ファイルやリンクの共有・転売・公開はご遠慮ください。""")


def validate():
    errs = []
    for lang, t in T.items():
        if not 0 < len(t["title"]) <= 140:
            errs.append(f"{lang}: title length {len(t['title'])}")
        if len(t["tags"]) != 13 or len(set(t["tags"])) != 13:
            errs.append(f"{lang}: {len(t['tags'])} tags (need 13 unique)")
        for tag in t["tags"]:
            if len(tag) > 20 or not TAG_OK.match(tag):
                errs.append(f"{lang}: bad tag {tag!r} ({len(tag)})")
        for word in ("ENGL", "ANGL", "ANGIEL", "INGL", "АНГЛ", "英語", "ENGEL"):
            if word in t["description"].upper():
                break
        else:
            errs.append(f"{lang}: description must say the files are in English")
    print("\n".join(errs) or f"all {len(T)} translations valid")
    return not errs


def upload(langs):
    if not validate():
        sys.exit("fix the errors above first")
    e = L.etsy()
    sid = e.get_token()["shop_id"]
    for lang in langs or list(T):
        t = T[lang]
        path = f"/shops/{sid}/listings/{LISTING_ID}/translations/{lang}"
        form = dict(title=t["title"], description=t["description"], tags=",".join(t["tags"]))
        have = e.request("GET", path)
        e.request("PUT" if have.get("title") else "POST", path, form=form)
        print(f"{lang}: translated", flush=True)


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["check"]
    validate() if cmd == "check" else upload(rest)
