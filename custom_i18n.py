"""Translations of the custom photo color-by-number listing (draft 4621704930).

    python custom_i18n.py check            # validate every language, no upload
    python custom_i18n.py upload [lang..]  # create/update the translations on Etsy
"""
import re
import sys

LISTING_ID = 4621704930
TAG_OK = re.compile(r"^[\w \-'™©®]+$")
CREDIT = {
    "fr": "Les photos d'exemple de cette annonce sont des photos libres de droits (CC0 / domaine public) de Wikimedia Commons.",
}

T = {}

T["fr"] = dict(
    title="Coloriage magique personnalisé à partir de votre photo, peinture par numéro mystère, famille animal couple paysage, Procreate + imprimable",
    tags=["coloriage magique", "peinture par numéro", "photo en coloriage", "coloriage perso", "coloriage procreate",
          "coloriage mystère", "cadeau personnalisé", "cadeau photo famille", "portrait animal", "cadeau couple",
          "coloriage paysage", "cadeau de noël", "coloriage photo"],
    description="""Transformez la photo que vous aimez en un coloriage magique unique ! Votre famille, votre animal, votre moitié, un voyage préféré ou un beau paysage : envoyez-moi la photo et je la transforme en page numérotée avec sa propre palette de couleurs, prête en 24 heures.

Offrez-le en CADEAU MYSTÈRE : la personne qui colorie ne sait pas ce que représente l'image avant qu'elle n'apparaisse peu à peu sous ses crayons. L'image finie est dans un dossier "réponse" séparé, pour ne rien gâcher.

COMMENT COMMANDER
1. Choisissez votre niveau et ajoutez au panier.
2. Après l'achat, envoyez votre photo dans la messagerie Etsy (fichier original en pleine taille, lumineux et net).
3. Je vérifie chaque page à la main et vous envoie le lien de téléchargement dans la messagerie Etsy sous 24 heures.

CHOISISSEZ VOTRE NIVEAU
- Relaxant : 16 couleurs, grandes zones. Idéal pour débuter et pour les enfants.
- Standard : 24 couleurs. Le choix le plus populaire.
- Détaillé : 36 couleurs, plus de détails. Pour les coloristes confirmés.

CE QUE VOUS RECEVEZ
- PDF prêts à imprimer en US Letter, A4 et poster 16x20
- Pages PNG numérotées pour Procreate / iPad : traits foncés, traits gris clair (ils disparaissent sous la peinture) et une version avec la palette imprimée en dessous
- Palette Procreate .swatches avec les couleurs dans l'ordre des numéros
- Nuancier numéroté et liste des codes hexadécimaux
- Dessin vectoriel SVG
- Un dossier RÉVÉLATION séparé avec l'image finie et les guides de couleurs

CONSEILS PHOTO
- Les photos lumineuses prises de jour donnent le meilleur résultat ; évitez les photos floues ou sombres.
- Les personnes, l'animal ou le paysage doivent remplir la plus grande partie de la photo.
- Les visages deviennent des formes de couleur simples, comme une peinture, pas un portrait photoréaliste. Les photos de famille en pied, les animaux, les voyages et les paysages donnent le plus beau résultat.
- Pas sûr de votre photo ? Envoyez-la quand même, je vous dirai avant de commencer.

IDÉAL POUR
Cadeaux de Noël, souvenirs de famille, amoureux des animaux et hommages, anniversaires de mariage, couples, grands-parents, souvenirs de voyage, anniversaires et tous ceux qui aiment colorier.

À NOTER
- Ceci est un article numérique. Rien n'est expédié.
- À l'achat, vous recevez un PDF avec les instructions de commande ; vos fichiers personnalisés suivent par la messagerie Etsy sous 24 heures.
- Votre photo sert uniquement à votre commande et est supprimée après la livraison. N'envoyez que des photos que vous avez le droit d'utiliser.
- Les couleurs peuvent varier légèrement selon les écrans et les imprimantes.
- Usage personnel uniquement. Merci de ne pas partager ni revendre les fichiers.
- Pas satisfait du résultat ? Écrivez-moi et je le refais avec une autre photo ou un autre niveau.

Pour des formes nettes et de plus jolis visages, votre photo est d'abord transformée en illustration avec un outil d'IA (Google Gemini), puis en page numérotée.

Les photos d'exemple de cette annonce sont des photos d'exemple générées par IA et des photos libres (CC0 / domaine public) de Wikimedia Commons.""")

T["de"] = dict(
    title="Malen nach Zahlen nach eigenem Foto, Mystery Ausmalbild, Familie Haustier Paar Landschaft, Procreate + zum Ausdrucken, Personalisiert",
    tags=["malen nach zahlen", "ausmalen nach zahlen", "foto als ausmalbild", "eigenes ausmalbild", "procreate ausmalbild",
          "mystery ausmalbild", "personalisiert", "familienfoto", "haustier portrait", "geschenk für paare",
          "landschaft malen", "weihnachtsgeschenk", "foto ausmalbild"],
    description="""Verwandle dein Lieblingsfoto in ein einzigartiges Malen-nach-Zahlen-Bild! Deine Familie, dein Haustier, dein Schatz, eine Lieblingsreise oder eine schöne Aussicht: Schick mir das Foto und ich mache daraus eine nummerierte Ausmalseite mit eigener Farbpalette, fertig innerhalb von 24 Stunden.

Als MYSTERY-GESCHENK: Wer ausmalt, weiß nicht, was das Bild zeigt, bis es langsam unter den Stiften erscheint. Das fertige Bild liegt in einem separaten Lösungsordner, damit nichts verraten wird.

SO BESTELLST DU
1. Wähle dein Level und lege es in den Warenkorb.
2. Schick mir nach dem Kauf dein Foto über Etsy-Nachrichten (Originaldatei in voller Größe, hell und scharf).
3. Ich prüfe jede Seite von Hand und schicke dir den Download-Link innerhalb von 24 Stunden über Etsy-Nachrichten.

WÄHLE DEIN LEVEL
- Entspannt: 16 Farben, größere Flächen. Ideal für Anfänger und Kinder.
- Standard: 24 Farben. Die beliebteste Wahl.
- Detailliert: 36 Farben, mehr Details. Für Geübte.

DAS BEKOMMST DU
- Druckfertige PDFs in US Letter, A4 und Poster 16x20
- Nummerierte PNG-Seiten für Procreate / iPad: dunkle Linien, hellgraue Linien (sie verschwinden unter der Farbe) und eine Version mit Farbpalette darunter
- Procreate-Palette (.swatches) mit den Farben in Nummernreihenfolge
- Nummerierte Farbkarte und Liste der Hex-Codes
- Skalierbare SVG-Linienzeichnung
- Ein separater LÖSUNGS-Ordner mit dem fertigen Bild und Farbvorlagen

FOTO-TIPPS
- Helle Tageslichtfotos funktionieren am besten; vermeide unscharfe oder dunkle Fotos.
- Die Menschen, das Tier oder die Aussicht sollten den Großteil des Fotos füllen.
- Gesichter werden zu einfachen Farbflächen, wie bei einem Gemälde, nicht fotorealistisch. Ganzkörper-Familienfotos, Haustiere, Reisefotos und Landschaften ergeben das schönste Ergebnis.
- Unsicher bei deinem Foto? Schick es trotzdem, ich sage dir Bescheid, bevor ich anfange.

PERFEKT FÜR
Weihnachtsgeschenke, Familienerinnerungen, Tierliebhaber und Erinnerungen an Haustiere, Jahrestage, Paare, Großeltern, Reiseerinnerungen, Geburtstage und alle, die gerne ausmalen.

BITTE BEACHTEN
- Dies ist ein digitaler Artikel. Es wird nichts verschickt.
- Beim Kauf erhältst du ein PDF mit der Bestellanleitung; deine persönlichen Dateien folgen innerhalb von 24 Stunden über Etsy-Nachrichten.
- Dein Foto wird nur für deine Bestellung verwendet und nach der Lieferung gelöscht. Bitte sende nur Fotos, die du verwenden darfst.
- Farben können auf Bildschirmen und Druckern leicht abweichen.
- Nur für den privaten Gebrauch. Bitte die Dateien nicht teilen oder weiterverkaufen.
- Nicht zufrieden? Schreib mir und ich mache es mit einem anderen Foto oder Level neu.

Für klare Formen und schönere Gesichter wird dein Foto zuerst mit einem KI-Bildwerkzeug (Google Gemini) in eine Illustration verwandelt und dann in deine nummerierte Seite.

Die Beispielfotos in diesem Angebot sind KI-generierte Beispielfotos und lizenzfreie Fotos (CC0 / gemeinfrei) von Wikimedia Commons.""")

T["es"] = dict(
    title="Colorear por números personalizado con tu foto, pintar por números misterio, familia mascota pareja paisaje, Procreate + imprimible",
    tags=["colorear por números", "pintar por números", "foto para colorear", "dibujo personalizado", "colorear procreate",
          "colorear misterio", "regalo personalizado", "regalo foto familia", "retrato de mascota", "regalo para pareja",
          "paisaje colorear", "regalo de navidad", "lámina para colorear"],
    description="""¡Convierte la foto que más quieres en un colorear por números único! Tu familia, tu mascota, tu pareja, un viaje favorito o un paisaje precioso: envíame la foto y la convierto en una página numerada con su propia paleta de colores, lista en 24 horas.

Regálalo como REGALO MISTERIO: quien colorea no sabe qué es la imagen hasta que aparece poco a poco bajo sus lápices. La imagen terminada va en una carpeta de solución aparte, para no estropear la sorpresa.

CÓMO PEDIR
1. Elige tu nivel y añádelo al carrito.
2. Después de la compra, envíame tu foto por los mensajes de Etsy (archivo original a tamaño completo, luminoso y nítido).
3. Reviso cada página a mano y te envío el enlace de descarga por mensajes de Etsy en 24 horas.

ELIGE TU NIVEL
- Relajante: 16 colores, zonas más grandes. Ideal para principiantes y niños.
- Estándar: 24 colores. La opción más popular.
- Detallado: 36 colores, más detalle. Para coloristas con experiencia.

QUÉ RECIBES
- PDF listos para imprimir en US Letter, A4 y póster 16x20
- Páginas PNG numeradas para Procreate / iPad: líneas oscuras, líneas gris claro (desaparecen bajo la pintura) y una versión con la paleta impresa debajo
- Paleta de Procreate (.swatches) con los colores en orden numérico
- Carta de colores numerada y lista de códigos hex
- Dibujo vectorial SVG escalable
- Una carpeta REVELACIÓN aparte con la imagen terminada y las guías de color

CONSEJOS PARA LA FOTO
- Las fotos con luz de día funcionan mejor; evita fotos borrosas u oscuras.
- Las personas, la mascota o el paisaje deben ocupar la mayor parte de la foto.
- Las caras se convierten en formas de color sencillas, como una pintura, no en un retrato fotorrealista. Las fotos familiares de cuerpo entero, mascotas, viajes y paisajes dan el mejor resultado.
- ¿No estás seguro de tu foto? Envíala igualmente y te aviso antes de empezar.

PERFECTO PARA
Regalos de Navidad, recuerdos familiares, amantes de las mascotas y homenajes, aniversarios, parejas, abuelos, recuerdos de viaje, cumpleaños y cualquiera a quien le guste colorear.

TEN EN CUENTA
- Es un artículo digital. No se envía nada físico.
- Al comprar recibes un PDF con las instrucciones del pedido; tus archivos personalizados llegan por mensajes de Etsy en 24 horas.
- Tu foto solo se usa para tu pedido y se borra después de la entrega. Envía solo fotos que tengas derecho a usar.
- Los colores pueden verse algo distintos según la pantalla y la impresora.
- Solo para uso personal. Por favor, no compartas ni revendas los archivos.
- ¿No te convence el resultado? Escríbeme y lo rehago con otra foto u otro nivel.

Para lograr formas limpias y caras más bonitas, tu foto se convierte primero en una ilustración con una herramienta de IA (Google Gemini) y después en tu página numerada.

Las fotos de ejemplo de este anuncio son fotos de muestra generadas con IA y fotos de licencia libre (CC0 / dominio público) de Wikimedia Commons.""")

T["it"] = dict(
    title="Colora per numeri personalizzato dalla tua foto, dipingi con i numeri misterioso, famiglia animale coppia paesaggio, Procreate + stampabile",
    tags=["colora per numeri", "dipingere con numeri", "foto da colorare", "disegno su misura", "colorare procreate",
          "colorare misterioso", "regalo su misura", "regalo foto famiglia", "ritratto animale", "regalo di coppia",
          "paesaggio colorare", "regalo di natale", "pagina da colorare"],
    description="""Trasforma la foto che ami in un colora per numeri unico! La tua famiglia, il tuo animale, la tua dolce metà, un viaggio preferito o un bel paesaggio: mandami la foto e la trasformo in una pagina numerata con la sua palette di colori, pronta in 24 ore.

Regalalo come REGALO MISTERIOSO: chi colora non sa cosa rappresenta l'immagine finché non appare piano piano sotto le matite. L'immagine finita è in una cartella soluzione separata, così niente sorprese rovinate.

COME ORDINARE
1. Scegli il livello e aggiungi al carrello.
2. Dopo l'acquisto, inviami la foto nei messaggi di Etsy (file originale a grandezza piena, luminoso e nitido).
3. Controllo ogni pagina a mano e ti invio il link per il download nei messaggi di Etsy entro 24 ore.

SCEGLI IL LIVELLO
- Rilassante: 16 colori, aree più grandi. Ideale per principianti e bambini.
- Standard: 24 colori. La scelta più amata.
- Dettagliato: 36 colori, più dettagli. Per chi ha esperienza.

COSA RICEVI
- PDF pronti da stampare in US Letter, A4 e poster 16x20
- Pagine PNG numerate per Procreate / iPad: linee scure, linee grigio chiaro (spariscono sotto il colore) e una versione con la palette stampata sotto
- Palette Procreate (.swatches) con i colori in ordine di numero
- Cartella colori numerata ed elenco dei codici esadecimali
- Disegno vettoriale SVG scalabile
- Una cartella RIVELAZIONE separata con l'immagine finita e le guide colori

CONSIGLI PER LA FOTO
- Le foto luminose con luce del giorno danno i risultati migliori; evita foto sfocate o scure.
- Le persone, l'animale o il paesaggio devono riempire gran parte della foto.
- I volti diventano semplici forme di colore, come in un dipinto, non un ritratto fotorealistico. Foto di famiglia a figura intera, animali, viaggi e paesaggi danno il risultato più bello.
- Non sei sicuro della tua foto? Inviala comunque e ti dico prima di iniziare.

PERFETTO PER
Regali di Natale, ricordi di famiglia, amanti degli animali e ricordi di animali scomparsi, anniversari, coppie, nonni, ricordi di viaggio, compleanni e chiunque ami colorare.

DA SAPERE
- Questo è un articolo digitale. Non viene spedito nulla.
- All'acquisto ricevi un PDF con le istruzioni per l'ordine; i tuoi file personalizzati arrivano nei messaggi di Etsy entro 24 ore.
- La tua foto viene usata solo per il tuo ordine e cancellata dopo la consegna. Invia solo foto che hai il diritto di usare.
- I colori possono apparire leggermente diversi su schermi e stampanti.
- Solo per uso personale. Per favore non condividere né rivendere i file.
- Non sei soddisfatto? Scrivimi e lo rifaccio con un'altra foto o un altro livello.

Per forme pulite e volti più belli, la tua foto viene prima trasformata in un'illustrazione con uno strumento di IA (Google Gemini) e poi nella tua pagina numerata.

Le foto di esempio in questo annuncio sono foto di esempio generate con IA e foto a licenza libera (CC0 / pubblico dominio) da Wikimedia Commons.""")

T["nl"] = dict(
    title="Kleuren op nummer van je eigen foto, mystery schilderen op nummer, gezin huisdier stel landschap, Procreate + printbaar, gepersonaliseerd",
    tags=["kleuren op nummer", "schilderen op nummer", "foto kleurplaat", "eigen kleurplaat", "procreate kleurplaat",
          "mystery kleurplaat", "gepersonaliseerd", "gezinsfoto cadeau", "huisdier portret", "cadeau voor koppel",
          "landschap kleuren", "kerstcadeau", "kleurplaat volwassen"],
    description="""Maak van je favoriete foto een unieke kleuren-op-nummer plaat! Je gezin, je huisdier, je partner, een favoriete reis of een prachtig uitzicht: stuur me de foto en ik maak er een genummerde kleurplaat van met een eigen kleurenpalet, klaar binnen 24 uur.

Geef het als MYSTERY CADEAU: wie kleurt, weet niet wat de afbeelding is tot die langzaam onder de potloden verschijnt. De afgewerkte afbeelding zit in een aparte oplossingsmap, dus niets wordt verklapt.

ZO BESTEL JE
1. Kies je niveau en voeg toe aan je winkelwagen.
2. Stuur na het afrekenen je foto via Etsy-berichten (origineel bestand op volle grootte, helder en scherp).
3. Ik controleer elke pagina met de hand en stuur je downloadlink binnen 24 uur via Etsy-berichten.

KIES JE NIVEAU
- Ontspannen: 16 kleuren, grotere vlakken. Ideaal voor beginners en kinderen.
- Standaard: 24 kleuren. De populairste keuze.
- Gedetailleerd: 36 kleuren, meer details. Voor ervaren kleurders.

WAT JE KRIJGT
- Printklare PDF's in US Letter, A4 en poster 16x20
- Genummerde PNG-pagina's voor Procreate / iPad: donkere lijnen, lichtgrijze lijnen (die verdwijnen onder de verf) en een versie met het palet eronder
- Procreate-palet (.swatches) met de kleuren op nummervolgorde
- Genummerde kleurenkaart en lijst met hexcodes
- Schaalbare SVG-lijntekening
- Een aparte ONTHULLING-map met de afgewerkte afbeelding en kleurgidsen

FOTOTIPS
- Heldere foto's bij daglicht werken het best; vermijd wazige of donkere foto's.
- De mensen, het dier of het uitzicht moeten het grootste deel van de foto vullen.
- Gezichten worden eenvoudige kleurvlakken, zoals in een schilderij, geen fotorealistisch portret. Gezinsfoto's ten voeten uit, huisdieren, reisfoto's en landschappen geven het mooiste resultaat.
- Twijfel je over je foto? Stuur hem gewoon, ik laat het je weten voordat ik begin.

PERFECT VOOR
Kerstcadeaus, familieherinneringen, dierenliefhebbers en herinneringen aan huisdieren, jubilea, stellen, grootouders, reisherinneringen, verjaardagen en iedereen die graag kleurt.

LET OP
- Dit is een digitaal artikel. Er wordt niets verzonden.
- Bij aankoop krijg je een PDF met bestelinstructies; je persoonlijke bestanden volgen binnen 24 uur via Etsy-berichten.
- Je foto wordt alleen voor je bestelling gebruikt en na levering verwijderd. Stuur alleen foto's die je mag gebruiken.
- Kleuren kunnen op schermen en printers iets afwijken.
- Alleen voor persoonlijk gebruik. Deel of verkoop de bestanden niet door.
- Niet tevreden? Stuur me een bericht en ik maak het opnieuw met een andere foto of een ander niveau.

Voor strakke vormen en mooiere gezichten wordt je foto eerst met een AI-beeldtool (Google Gemini) omgezet in een illustratie en daarna in je genummerde pagina.

De voorbeeldfoto's in deze advertentie zijn door AI gemaakte voorbeeldfoto's en vrij te gebruiken foto's (CC0 / publiek domein) van Wikimedia Commons.""")

T["pt"] = dict(
    title="Colorir por números personalizado com sua foto, pintura por números mistério, família pet casal paisagem, Procreate + imprimível",
    tags=["colorir por números", "pintura por números", "foto para colorir", "desenho sob medida", "colorir procreate",
          "colorir mistério", "presente exclusivo", "presente com foto", "retrato de pet", "presente para casal",
          "paisagem colorir", "presente de natal", "página para colorir"],
    description="""Transforme a foto que você ama em um colorir por números único! Sua família, seu pet, seu amor, uma viagem favorita ou uma linda paisagem: envie a foto e eu a transformo em uma página numerada com sua própria paleta de cores, pronta em 24 horas.

Dê como PRESENTE MISTÉRIO: quem colore não sabe qual é a imagem até ela aparecer aos poucos sob os lápis. A imagem pronta vem em uma pasta de resposta separada, para não estragar a surpresa.

COMO PEDIR
1. Escolha seu nível e adicione ao carrinho.
2. Depois da compra, envie sua foto pelas mensagens do Etsy (arquivo original em tamanho cheio, claro e nítido).
3. Confiro cada página à mão e envio seu link de download pelas mensagens do Etsy em até 24 horas.

ESCOLHA SEU NÍVEL
- Relaxante: 16 cores, áreas maiores. Ótimo para iniciantes e crianças.
- Padrão: 24 cores. A escolha mais popular.
- Detalhado: 36 cores, mais detalhes. Para quem já tem experiência.

O QUE VOCÊ RECEBE
- PDFs prontos para imprimir em US Letter, A4 e pôster 16x20
- Páginas PNG numeradas para Procreate / iPad: linhas escuras, linhas cinza-claro (somem sob a tinta) e uma versão com a paleta impressa embaixo
- Paleta do Procreate (.swatches) com as cores em ordem numérica
- Cartela de cores numerada e lista de códigos hex
- Desenho vetorial SVG escalável
- Uma pasta REVELAÇÃO separada com a imagem pronta e os guias de cores

DICAS DE FOTO
- Fotos claras com luz do dia funcionam melhor; evite fotos borradas ou escuras.
- As pessoas, o pet ou a paisagem devem ocupar a maior parte da foto.
- Os rostos viram formas de cor simples, como numa pintura, não um retrato fotorrealista. Fotos de família de corpo inteiro, pets, viagens e paisagens dão o resultado mais bonito.
- Não tem certeza da sua foto? Envie mesmo assim que eu aviso antes de começar.

PERFEITO PARA
Presentes de Natal, lembranças de família, amantes de pets e homenagens, aniversários de casamento, casais, avós, lembranças de viagem, aniversários e quem adora colorir.

OBSERVAÇÕES
- Este é um item digital. Nada é enviado pelo correio.
- Na compra você recebe um PDF com as instruções do pedido; seus arquivos personalizados chegam pelas mensagens do Etsy em até 24 horas.
- Sua foto é usada apenas no seu pedido e apagada após a entrega. Envie apenas fotos que você tem direito de usar.
- As cores podem variar um pouco entre telas e impressoras.
- Somente para uso pessoal. Por favor, não compartilhe nem revenda os arquivos.
- Não gostou do resultado? Me mande uma mensagem e eu refaço com outra foto ou outro nível.

Para formas limpas e rostos mais bonitos, sua foto é primeiro transformada em ilustração com uma ferramenta de IA (Google Gemini) e depois na sua página numerada.

As fotos de exemplo deste anúncio são fotos de exemplo geradas por IA e fotos de licença livre (CC0 / domínio público) do Wikimedia Commons.""")

T["pl"] = dict(
    title="Kolorowanka z numerami z Twojego zdjęcia, malowanie po numerach z niespodzianką, rodzina zwierzak para krajobraz, Procreate + do druku",
    tags=["malowanie numerami", "kolorowanie numerami", "zdjęcie kolorowanka", "własna kolorowanka", "procreate malowanie",
          "kolorowanka zagadka", "prezent z imieniem", "prezent ze zdjęciem", "portret zwierzaka", "prezent dla pary",
          "malowanie krajobraz", "prezent świąteczny", "kolorowanka dorośli"],
    description="""Zamień ulubione zdjęcie w niepowtarzalną kolorowankę z numerami! Twoja rodzina, zwierzak, ukochana osoba, ulubiona podróż albo piękny widok: wyślij mi zdjęcie, a zrobię z niego ponumerowaną stronę z własną paletą kolorów, gotową w 24 godziny.

Podaruj jako PREZENT NIESPODZIANKĘ: osoba kolorująca nie wie, co przedstawia obrazek, dopóki nie wyłoni się spod kredek. Gotowy obraz jest w osobnym folderze z rozwiązaniem, więc nic nie zostanie zdradzone.

JAK ZAMÓWIĆ
1. Wybierz poziom i dodaj do koszyka.
2. Po zakupie wyślij zdjęcie w wiadomościach Etsy (oryginalny plik w pełnym rozmiarze, jasny i ostry).
3. Sprawdzam każdą stronę ręcznie i wysyłam link do pobrania w wiadomościach Etsy w ciągu 24 godzin.

WYBIERZ POZIOM
- Relaks: 16 kolorów, większe pola. Idealny dla początkujących i dzieci.
- Standard: 24 kolory. Najczęstszy wybór.
- Szczegółowy: 36 kolorów, więcej detali. Dla doświadczonych.

CO OTRZYMUJESZ
- Pliki PDF gotowe do druku w formatach US Letter, A4 i plakat 16x20
- Ponumerowane strony PNG do Procreate / iPada: ciemne linie, jasnoszare linie (znikają pod farbą) oraz wersja z paletą pod spodem
- Paleta Procreate (.swatches) z kolorami w kolejności numerów
- Ponumerowana karta kolorów i lista kodów hex
- Skalowalny rysunek wektorowy SVG
- Osobny folder ODSŁONA z gotowym obrazem i przewodnikami kolorów

WSKAZÓWKI DO ZDJĘCIA
- Najlepiej sprawdzają się jasne zdjęcia przy świetle dziennym; unikaj nieostrych i ciemnych.
- Ludzie, zwierzak lub widok powinni wypełniać większą część zdjęcia.
- Twarze zamieniają się w proste plamy koloru, jak na obrazie, a nie fotorealistyczny portret. Najpiękniej wychodzą rodzinne zdjęcia całej postaci, zwierzaki, podróże i krajobrazy.
- Nie wiesz, czy zdjęcie się nada? Wyślij je, a dam znać, zanim zacznę.

IDEALNE NA
Prezenty świąteczne, rodzinne wspomnienia, miłośników zwierząt i pamiątki po pupilach, rocznice, pary, dziadków, wspomnienia z podróży, urodziny i dla każdego, kto lubi kolorować.

WAŻNE
- To produkt cyfrowy. Nic nie jest wysyłane.
- Po zakupie otrzymasz PDF z instrukcją zamówienia; Twoje pliki przyjdą w wiadomościach Etsy w ciągu 24 godzin.
- Twoje zdjęcie służy tylko do Twojego zamówienia i jest usuwane po dostawie. Wysyłaj tylko zdjęcia, do których masz prawo.
- Kolory mogą się nieco różnić na ekranach i drukarkach.
- Tylko do użytku osobistego. Proszę nie udostępniać ani nie odsprzedawać plików.
- Nie podoba Ci się efekt? Napisz do mnie, a zrobię to ponownie z innym zdjęciem lub poziomem.

Aby uzyskać wyraźne kształty i ładniejsze twarze, Twoje zdjęcie jest najpierw zamieniane w ilustrację narzędziem AI (Google Gemini), a potem w ponumerowaną stronę.

Przykładowe zdjęcia w tej ofercie to przykładowe zdjęcia wygenerowane przez AI oraz zdjęcia na wolnej licencji (CC0 / domena publiczna) z Wikimedia Commons.""")

T["ru"] = dict(
    title="Раскраска по номерам по вашему фото, картина по номерам сюрприз, семья питомец пара пейзаж, Procreate + для печати, персональный подарок",
    tags=["раскраска по номерам", "картина по номерам", "раскраска из фото", "своя раскраска", "раскраска procreate",
          "раскраска сюрприз", "именной подарок", "подарок с фото", "портрет питомца", "подарок для пары",
          "раскраска пейзаж", "подарок на новый год", "раскраска антистресс"],
    description="""Превратите любимое фото в уникальную раскраску по номерам! Ваша семья, питомец, любимый человек, памятное путешествие или красивый пейзаж: пришлите мне фото, и я сделаю из него пронумерованную страницу с собственной палитрой цветов, готовую за 24 часа.

Подарите как ПОДАРОК-СЮРПРИЗ: тот, кто раскрашивает, не знает, что на картинке, пока она постепенно не проявится под карандашами. Готовая картинка лежит в отдельной папке с ответом, так что сюрприз не испортится.

КАК ЗАКАЗАТЬ
1. Выберите уровень и добавьте в корзину.
2. После покупки отправьте фото в сообщениях Etsy (оригинальный файл в полном размере, светлый и чёткий).
3. Я проверяю каждую страницу вручную и присылаю ссылку на скачивание в сообщениях Etsy в течение 24 часов.

ВЫБЕРИТЕ УРОВЕНЬ
- Расслабляющий: 16 цветов, крупные области. Для начинающих и детей.
- Стандартный: 24 цвета. Самый популярный выбор.
- Детальный: 36 цветов, больше деталей. Для опытных.

ЧТО ВЫ ПОЛУЧИТЕ
- PDF для печати в форматах US Letter, A4 и постер 16x20
- Пронумерованные страницы PNG для Procreate / iPad: тёмные линии, светло-серые линии (исчезают под краской) и версия с палитрой внизу
- Палитра Procreate (.swatches) с цветами по порядку номеров
- Пронумерованная карта цветов и список hex-кодов
- Масштабируемый векторный рисунок SVG
- Отдельная папка ОТВЕТ с готовой картинкой и цветовыми подсказками

СОВЕТЫ ПО ФОТО
- Лучше всего подходят светлые дневные фото; избегайте размытых и тёмных.
- Люди, питомец или пейзаж должны занимать большую часть фото.
- Лица превращаются в простые цветовые пятна, как на картине, а не в фотореалистичный портрет. Лучше всего получаются семейные фото в полный рост, питомцы, путешествия и пейзажи.
- Не уверены в фото? Всё равно пришлите, я скажу до начала работы.

ИДЕАЛЬНО ДЛЯ
Новогодних и рождественских подарков, семейных воспоминаний, любителей животных и памяти о питомцах, годовщин, пар, бабушек и дедушек, воспоминаний о путешествиях, дней рождения и всех, кто любит раскрашивать.

ОБРАТИТЕ ВНИМАНИЕ
- Это цифровой товар. Ничего не отправляется по почте.
- При покупке вы получаете PDF с инструкцией по заказу; ваши персональные файлы придут в сообщениях Etsy в течение 24 часов.
- Ваше фото используется только для вашего заказа и удаляется после доставки. Присылайте только фото, которые вы вправе использовать.
- Цвета могут немного отличаться на разных экранах и принтерах.
- Только для личного использования. Пожалуйста, не распространяйте и не перепродавайте файлы.
- Не понравился результат? Напишите мне, и я переделаю с другим фото или уровнем.

Чтобы формы были чёткими, а лица красивее, ваше фото сначала превращается в иллюстрацию с помощью ИИ-инструмента (Google Gemini), а затем в пронумерованную страницу.

Примеры фото в этом объявлении — образцы, созданные ИИ, и фото под свободной лицензией (CC0 / общественное достояние) с Wikimedia Commons.""")

T["sv"] = dict(
    title="Måla efter nummer från ditt eget foto, mystisk färgläggning, familj husdjur par landskap, Procreate + utskrivbar, personlig present",
    tags=["måla efter nummer", "färglägg med nummer", "foto till målarbild", "egen målarbild", "procreate målarbild",
          "mystisk målarbild", "personlig present", "familjefoto present", "husdjursporträtt", "present till par",
          "landskap målarbild", "julklapp", "målarbild vuxen"],
    description="""Gör ditt favoritfoto till en unik måla-efter-nummer-bild! Din familj, ditt husdjur, din partner, en favoritresa eller en vacker utsikt: skicka fotot så gör jag en numrerad målarbild med egen färgpalett, klar inom 24 timmar.

Ge den som MYSTISK PRESENT: den som färglägger vet inte vad bilden föreställer förrän den långsamt växer fram under pennorna. Den färdiga bilden ligger i en separat facitmapp, så inget avslöjas.

SÅ BESTÄLLER DU
1. Välj nivå och lägg i varukorgen.
2. Skicka ditt foto i Etsy-meddelanden efter köpet (originalfil i full storlek, ljus och skarp).
3. Jag kontrollerar varje sida för hand och skickar nedladdningslänken i Etsy-meddelanden inom 24 timmar.

VÄLJ NIVÅ
- Avslappnad: 16 färger, större ytor. Perfekt för nybörjare och barn.
- Standard: 24 färger. Det populäraste valet.
- Detaljerad: 36 färger, mer detaljer. För vana färgläggare.

DETTA FÅR DU
- Utskriftsklara PDF:er i US Letter, A4 och affisch 16x20
- Numrerade PNG-sidor för Procreate / iPad: mörka linjer, ljusgrå linjer (de försvinner under färgen) och en version med paletten under
- Procreate-palett (.swatches) med färgerna i nummerordning
- Numrerad färgkarta och lista med hexkoder
- Skalbar SVG-linjeteckning
- En separat AVSLÖJANDE-mapp med den färdiga bilden och färgguider

FOTOTIPS
- Ljusa foton i dagsljus blir bäst; undvik suddiga eller mörka foton.
- Personerna, djuret eller utsikten ska fylla större delen av fotot.
- Ansikten blir enkla färgfält, som i en målning, inte ett fotorealistiskt porträtt. Helfigursfoton av familjen, husdjur, resefoton och landskap ger det finaste resultatet.
- Osäker på ditt foto? Skicka det ändå så säger jag till innan jag börjar.

PERFEKT FÖR
Julklappar, familjeminnen, djurvänner och minnen av husdjur, årsdagar, par, mor- och farföräldrar, reseminnen, födelsedagar och alla som gillar att färglägga.

BRA ATT VETA
- Detta är en digital produkt. Inget skickas.
- Vid köpet får du en PDF med beställningsinstruktioner; dina personliga filer kommer i Etsy-meddelanden inom 24 timmar.
- Ditt foto används bara för din beställning och raderas efter leverans. Skicka bara foton som du har rätt att använda.
- Färger kan se lite olika ut på skärmar och skrivare.
- Endast för personligt bruk. Dela eller sälj inte vidare filerna.
- Inte nöjd? Skriv till mig så gör jag om den med ett annat foto eller en annan nivå.

För tydliga former och finare ansikten görs ditt foto först om till en illustration med ett AI-bildverktyg (Google Gemini) och sedan till din numrerade sida.

Exempelfotona i denna annons är AI-genererade exempelfoton och fritt licensierade foton (CC0 / allmän egendom) från Wikimedia Commons.""")

T["ja"] = dict(
    title="写真から作るオーダーメイド塗り絵 数字で塗るぬりえ ミステリー 家族 ペット カップル 風景 Procreate 印刷用 名入れギフト",
    tags=["数字塗り絵", "ナンバーペイント", "写真から塗り絵", "オーダー塗り絵", "procreate塗り絵",
          "ミステリー塗り絵", "名入れギフト", "家族写真ギフト", "ペット似顔絵", "カップルギフト",
          "風景塗り絵", "クリスマスギフト", "大人の塗り絵"],
    description="""大切な写真が、世界にひとつだけの「数字で塗るぬりえ」になります！ご家族、ペット、パートナー、思い出の旅行、美しい景色など、写真を送っていただければ、専用カラーパレット付きの番号入りぬりえページを24時間以内にお作りします。

ミステリーギフトにも：塗る人は、色鉛筆の下から少しずつ絵が現れるまで何の絵かわかりません。完成イメージは別フォルダの「答え」に入っているので、ネタバレの心配はありません。

ご注文方法
1. レベルを選んでカートに入れてください。
2. ご購入後、Etsyのメッセージで写真をお送りください（明るくピントの合った、元のサイズの画像ファイル）。
3. すべてのページを手作業で確認し、24時間以内にEtsyのメッセージでダウンロードリンクをお送りします。

レベルを選べます
- リラックス：16色、大きめのエリア。初心者やお子様に。
- スタンダード：24色。いちばん人気。
- 細密：36色、より細かく。経験者向け。

お届け内容
- 印刷用PDF（USレター、A4、16x20ポスター）
- Procreate / iPad用の番号入りPNG：濃い線、薄いグレーの線（塗ると目立たなくなります）、パレット付きの3種類
- 番号順に並んだProcreateパレット（.swatches）
- 番号付きカラー見本カードとHEXコード一覧
- 拡大縮小できるSVG線画
- 完成イメージとカラーガイドが入った別フォルダ「答え」

写真選びのコツ
- 明るい日中の写真がおすすめです。ぼやけた写真や暗い写真は避けてください。
- 人物・ペット・景色が写真の大部分を占めるものが向いています。
- お顔は写真のようなリアルな肖像ではなく、絵画のようなシンプルな色の形になります。全身の家族写真、ペット、旅行写真、風景がいちばんきれいに仕上がります。
- 写真に迷ったら、まずはお送りください。作業前にご相談します。

こんな方に
クリスマスギフト、家族の思い出、ペット好きの方やペットのメモリアル、記念日、カップル、祖父母へのプレゼント、旅の思い出、お誕生日、ぬりえが好きなすべての方に。

ご注意
- デジタル商品です。現物の発送はありません。
- ご購入時にご注文方法のPDFが届きます。オーダー品のファイルは24時間以内にEtsyのメッセージでお送りします。
- お預かりした写真はご注文にのみ使用し、お届け後に削除します。使用する権利のある写真のみお送りください。
- 画面やプリンターにより色の見え方が多少異なる場合があります。
- 個人利用に限ります。ファイルの共有・転売はご遠慮ください。
- 仕上がりにご満足いただけない場合はご連絡ください。別の写真やレベルで作り直します。

きれいな形と自然なお顔に仕上げるため、お写真はまずAI画像ツール（Google Gemini）でイラストに変換してから、番号入りページにします。

この商品ページの見本写真は、AIで生成したサンプル写真と、Wikimedia Commonsの自由ライセンス（CC0／パブリックドメイン）の写真です。""")


def validate(lang, t):
    errs = []
    if not 0 < len(t["title"]) <= 140:
        errs.append(f"title length {len(t['title'])}")
    if len(t["tags"]) != 13 or len(set(t["tags"])) != 13:
        errs.append(f"{len(t['tags'])} tags / {len(set(t['tags']))} unique")
    for tag in t["tags"]:
        if len(tag) > 20 or not TAG_OK.match(tag):
            errs.append(f"bad tag {tag!r} ({len(tag)})")
    return [f"{lang}: {e}" for e in errs]


def check(langs):
    errs = [e for lang in langs for e in validate(lang, T[lang])]
    print("\n".join(errs) or f"all translations valid ({', '.join(langs)})")
    return not errs


def upload(langs):
    import etsy_api as e
    if not check(langs):
        sys.exit("fix the errors above first")
    sid = e.get_token()["shop_id"]
    for lang in langs:
        t = T[lang]
        path = f"/shops/{sid}/listings/{LISTING_ID}/translations/{lang}"
        form = dict(title=t["title"], description=t["description"], tags=",".join(t["tags"]))
        try:
            have = e.request("GET", path)
        except Exception:
            have = {}
        e.request("PUT" if have.get("title") else "POST", path, form=form)
        print(f"{lang}: translated", flush=True)


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["check"]
    {"check": check, "upload": upload}[cmd](rest or list(T))
