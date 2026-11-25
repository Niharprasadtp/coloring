# Etsy listing: Large Print Christmas Puzzle Book

**Files to upload:** `output/Large_Print_Christmas_Puzzle_Book_Letter.pdf`, `output/Large_Print_Christmas_Puzzle_Book_A4.pdf`

**Price:** $4.99. At launch, also run a 25% off sale so buyers see a reduced price.
**Category:** Type "puzzle" in Etsy's category box and choose the most specific match it offers (for example Toys & Games > Games & Puzzles > Puzzles). Do not use a general "Paper" category.
**Attributes:** fill in every one Etsy shows: Holiday = Christmas, Occasion if offered, and Digital download.
**Shop section:** Puzzle Books (create it once; future Winter, Spring, etc. books go here).
**Photos (in this order):** `output/listing/01_hero.jpg` ... `05_pages.jpg` (run `python make_listing_images.py`)

## Title (136 characters; the first 40 are "Large Print Christmas Puzzle Book PDF, 5")
Large Print Christmas Puzzle Book PDF, 52 Printable Holiday Brain Games for Adults & Seniors, Sudoku Word Search Mazes, Instant Download

## Tags (13 tags, each a 2-4 word buyer phrase of up to 20 characters)
large print puzzles, senior activity book, large print sudoku, xmas word search, holiday brain games,
nursing home games, printable puzzle pdf, gift for grandma, christmas sudoku, senior activities,
puzzles for adults, christmas printable, cryptogram puzzles

(Etsy matches words across the title and tags, so "christmas word search" is covered by the title's "Christmas" plus "Word Search".)

## Description

Screen-free Christmas fun in big, easy-to-read print. 52 relaxing puzzles to print at home, one puzzle per page, with bold lines and large letters and numbers.

WHAT'S INSIDE
• 6 Mini Sudoku (6x6) and 8 classic Sudoku (9x9)
• 12 Christmas word searches with 13x13 grids and big letters
• 10 holiday mazes
• 10 Carol Code-Breakers: decode a line from a classic Christmas carol
• 3 pages of Number Patterns ("what comes next?")
• 3 pages of Christmas Word Scrambles (30 words)
• A How to Play page and a full answer key with every solution

EVERY PUZZLE IS CHECKED
Each puzzle was checked by computer before it went into the book:
• Every Sudoku has exactly one solution and can be solved with no guessing
• Every maze has exactly one route from start to finish
• Every word in a word search appears exactly once
• Every scrambled word has only one possible answer
• Every number pattern has only one sensible next number

EASY START, GENTLE CHALLENGE
The puzzles start easy and get a little harder as you go. Each page is marked Easy or Medium.

GREAT FOR
• Quiet winter evenings, with a cup of tea
• Grandparents, parents and puzzle lovers
• Senior centers, care homes and activity groups
• Family gatherings and holiday travel
• A thoughtful last-minute gift or stocking stuffer (print and staple, or put the pages in a folder with a ribbon)

YOU WILL RECEIVE
• US Letter PDF (8.5 x 11 in), 76 pages
• A4 PDF (210 x 297 mm), 76 pages

This is a digital download. No physical item will be shipped. Print as many copies as you need for your household.

HOW IT WORKS
1. Buy and download the PDF from your Etsy Purchases page
2. Print at home or at a print shop (black and white works fine)
3. Grab a pencil and enjoy

TERMS OF USE
For personal use, and for use within one family, classroom, senior center or care home (you may print copies for your own residents or group members). Please do not resell, share or post the files.

---

## Before you press Publish
- [ ] All 5 photos uploaded, with the hero first
- [ ] Final title, all 13 tags, category, every attribute, shop section
- [ ] Both PDFs attached (Letter + A4)
- [ ] 25% sale set up
- [ ] Publish between 7:30 PM and 12:30 AM IST (US morning to early afternoon)
- [ ] Turn on Etsy Ads for THIS listing only, $1/day for 10-14 days
- [ ] After 3-4 days: Shop Manager > Stats > search terms. Put the real buyer phrases into the tags.

## Wording rules (Etsy and FTC)
Do not use: "improves memory", "prevents dementia", "brain health", "cognitive", "therapy" or any other health claim.
Safe wording: "brain games", "relaxing", "screen-free", "keeps your mind busy", "easy to read".

## Gemini prompts for listing photos

Ask Gemini for **blank** white paper. I will put the real book pages onto the paper, so the photos show exactly what the buyer gets. Gemini can't draw a correct Sudoku or word search; any puzzle it draws will have wrong numbers or letters.

Size: landscape, 4:3 (for example 2400 x 1800). Save the images in `puzzle_book/listing_bg/`.

1. **Hero (`hero_table.png`)**
   > Photorealistic top-down photo of a cozy wooden table at Christmas. Two blank white sheets of printer paper lie side by side in the center, completely empty with no text or marks. Around the edges: a yellow pencil, reading glasses, a cup of tea, pine branches, a few red and gold ornaments, warm fairy lights softly out of focus. Warm, soft daylight. 4:3 landscape. No text, no logos, no hands.

2. **Hands (`hands_pencil.png`)**
   > Photorealistic close-up of an older woman's hands holding a pencil over a single blank white sheet of paper on a wooden table, the paper completely empty. A mug of cocoa and a small Christmas tree are softly blurred in the background. Warm cozy light. 4:3 landscape. No text anywhere.

3. **Group activity (`group_table.png`)**
   > Photorealistic photo of a bright community room table decorated for Christmas, with four blank white sheets of paper and pencils at four places, a festive table runner, a plate of cookies. No people's faces visible. Paper completely blank. 4:3 landscape. No text.

4. **Gift (`gift_folder.png`)**
   > Photorealistic flat lay of a stack of blank white printed pages tied with a red velvet ribbon, next to a wrapped gift, pine sprigs and a candle, on a cream linen tablecloth. Top page completely blank. 4:3 landscape. No text.
