# Personalized kids car coloring book

Etsy draft 4626293742 (₹599). 62 pages: personalized cover, "belongs to" page, driver's license,
checklist, 50 car pages with the child's name on a license plate, 5 color-by-number pages,
"design your car" page and a certificate.

## Filling an order

1. Copy the child's name from the order's personalization ("Child's name").
2. Build the book (about 20 s):

   ```
   cd coloring/kids_car_book
   ../.venv/Scripts/python.exe make_book.py "Name" --preview
   ```

3. Open `../output/kids_car_book/<Name>/CHECK_preview.png` and check the spelling on the cover,
   plate and certificate.
4. Upload the two PDFs (Letter + A4, ~11 MB each) to Google Drive, share as "anyone with the
   link", and send the link in Etsy Messages. Mark the order complete.

Names: max 16 characters, Latin letters (accents like é, ü are fine). Hindi or other scripts are
refused with a clear message; ask the buyer for a Latin spelling.

## Files

- `prepare_art.py` – one-time: cleans the 50 chosen pages from the 100-car PDF and the 5
  color-by-number pages into `art/` (git-ignored, paid art). Pages with brand names or logos are left out.
- `make_book.py` – builds one personalized book.
- `make_listing.py photos|text|upload|update` – Etsy photos, text, checkout PDF, draft.
- `fonts/LuckiestGuy-Regular.ttf` – Apache 2.0, free for commercial use.
