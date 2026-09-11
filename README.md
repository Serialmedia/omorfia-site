# Omorfia Salon & Day Spa — omorfiapk.com

Static multi-page site, built for local SEO. Fifteen pages, each targeting a money search
("hair salon poughkeepsie", "massage poughkeepsie", etc.), with DaySpa LocalBusiness +
Service + FAQPage + Breadcrumb schema on every page, sitemap.xml, robots.txt, clean URLs.

## Before deploying — one required edit
Every "Book" button currently points to the placeholder `REPLACE_BOOKING_URL`.
Find-and-replace it across all .html files with the Boulevard self-booking link
(GitHub web editor: press `.` in the repo to open VS Code web, then global find/replace).

## Deploy (same pipeline as the KBG hub)
1. New GitHub repo (e.g. `omorfia-site`) → upload everything in this folder.
2. Vercel → Add New Project → import the repo → Deploy (static, no build settings).
3. Vercel → Domains → add `omorfiapk.com` → update the A/CNAME records at GoDaddy
   (this moves the domain off Base44 — the old site is replaced the moment DNS flips).
4. Google Search Console → add/verify omorfiapk.com → submit `sitemap.xml`.

## Local SEO checklist (this is where rankings are actually won)
- [ ] Confirm hours match the Google Business Profile letter-for-letter
      (site says Open Daily 9 AM–8 PM, schema declares all 7 days 9–8; if Sunday hours differ, fix in build.py).
- [ ] Set omorfiapk.com as the website on the Google Business Profile.
- [ ] 301-redirect omorfianewyork.com AND omorfiadayspa.com → omorfiapk.com (the old duplicate site is
      splitting your local signals — this is the single biggest cleanup available).
- [ ] Same name/address/phone everywhere: GBP, Yelp, Facebook, Instagram bio, Chamber listing.
- [ ] Footer link from kyriacoubeauty.com and the other KBG sites to omorfiapk.com.
- [ ] Reviews: ask every happy guest for a Google review; reply to all of them.

## Editing
`build.py` (one level up in the working copy) regenerates every page from one data file —
copy, prices, FAQ answers, hours, phone all live there. Edit → `python3 build.py` → commit.

## v2 — photo-forward upgrade (Marion-style structure)
- New pages: /wedding/ (bridal — high-value local SEO), /specials/ (new-guest offer funnel),
  /gift-cards/, /reviews/. Nav now has Salon / Spa / About dropdowns + utility bar.
- PHOTOS: currently stock placeholders hotlinked from Unsplash (fine for launch, but replace
  with real Omorfia photos ASAP — real photos convert better and help local SEO). To swap:
  put files in /images/ and change the IMG urls at the top of build.py, then rebuild.
- GIFT CARDS: buttons use the REPLACE_GIFTCARD_URL placeholder — Boulevard sells gift cards
  online; paste that link (or set it to the booking link).
- REVIEWS: the quotes on / and /reviews/ are shortened samples — replace with real Google
  reviews (copy 3–6 favorites into REVIEWS in build.py).

- KYRIACOU dropdown: 'Kyriacou Cosmetics' temporarily points to kyriacoubeauty.com — swap to the Shopify launch URL when it goes live (one line in build.py).
