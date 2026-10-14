#!/usr/bin/env python3
"""Omorfia — v2: photo-forward multi-page site (upgraded Marion-style structure).
Edit constants, run `python3 build.py`, deploy /site."""
import json, os, re, html

DOMAIN   = "https://www.omorfiabeauty.nyc"   # must match the host Vercel serves (apex 30x -> www)
BOOK_URL = "#book"      # Boulevard self-booking link
GIFT_URL = "#gift"     # Boulevard gift card link (or leave = BOOK_URL)
NAME     = "Omorfia Salon & Day Spa"
ALT_NAME = "Omorfia Salon & Spa"              # name as it appears on the Google Business Profile
STREET   = "751 Dutchess Turnpike"
CITY     = "Poughkeepsie"
STATE    = "NY"
ZIP      = "12603"
PHONE    = "(845) 694-4952"
PHONE_TEL= "+18456944952"
EMAIL    = "Stavros@kyriacoubeauty.com"
GEO      = (41.7005477, -73.8771062)
PLACE_ID = "ChIJa3T8WRM_3YkR99abqa-Z1dQ"
MAPS_URL = f"https://www.google.com/maps/place/?q=place_id:{PLACE_ID}"
FOUNDED  = "2024-07"
PRICE_RANGE = "$20 - $450"
SAMEAS   = ["https://www.instagram.com/omorfiadayspa/",
            "https://www.yelp.com/biz/omorfia-salon-and-spa-poughkeepsie",
            MAPS_URL]
# Nearby towns we draw guests from — used for areaServed schema and the "serving" line.
NEARBY   = ["Poughkeepsie","Hyde Park","Wappingers Falls","LaGrange","Pleasant Valley",
            "Fishkill","Hopewell Junction","Rhinebeck","Beacon","New Paltz","Highland"]
def slugify(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
OUT = os.path.join(os.path.dirname(__file__), "site")
TODAY = __import__("datetime").date.today().isoformat()

# Per-page social image (falls back to the s08 slide).
OG_IMG = {"":"/images/slides/s08.jpg","hair":"/images/home-hair.jpg","nails":"/images/home-nails.jpg",
          "massage":"/images/home-massage.jpg","facials":"/images/home-facials.jpg",
          "tanning":"/images/home-tanning.jpg","makeup":"/images/home-makeup.jpg",
          "team":"/images/team/group.jpg","about":"/images/about/a01-interior.jpg"}

U = "https://images.unsplash.com/"
Q = "?q=80&w=1600&auto=format&fit=crop"
# Hero fallbacks are local (the slideshow layers over them); no third-party hotlinks.
# All heroes fall back to the preloaded first slide so no page pays for a second hero image.
IMG = {k:"/images/slides/s08.jpg" for k in ("hero","hair","nails","massage","facials","tanning","makeup","wedding","feature")}

# ------------------------------------------------------------------ schema
def biz_node():
    return {"@type":["DaySpa","HairSalon","NailSalon","BeautySalon"],
        "@id":DOMAIN+"/#business","name":NAME,"alternateName":ALT_NAME,"url":DOMAIN+"/",
        "logo":DOMAIN+"/favicon.svg",
        "image":[DOMAIN+"/images/slides/s08.jpg",DOMAIN+"/images/about/a03-exterior.jpg",
                 DOMAIN+"/images/about/a01-interior.jpg"],
        "telephone":PHONE_TEL,"email":EMAIL,"priceRange":PRICE_RANGE,
        "address":{"@type":"PostalAddress","streetAddress":STREET,"addressLocality":CITY,
                   "addressRegion":STATE,"postalCode":ZIP,"addressCountry":"US"},
        "geo":{"@type":"GeoCoordinates","latitude":GEO[0],"longitude":GEO[1]},
        "hasMap":MAPS_URL,
        "areaServed":[{"@type":"City","name":f"{t}, NY"} for t in NEARBY]
                     +[{"@type":"AdministrativeArea","name":"Dutchess County, NY"},
                       {"@type":"Place","name":"Hudson Valley, NY"}],
        "openingHoursSpecification":[{"@type":"OpeningHoursSpecification",
            "dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens":"09:00","closes":"20:00"}],
        "foundingDate":FOUNDED,
        "currenciesAccepted":"USD","paymentAccepted":"Cash, Credit Card, Gift Card",
        "sameAs":SAMEAS,
        "parentOrganization":{"@type":"Organization","name":"Kyriacou Beauty Group",
                              "url":"https://kyriacoubeauty.com"},
        "slogan":"Where Beauty Meets Relaxation",
        "knowsAbout":["Hair salon","Hair color","Balayage","Hair extensions","Massage therapy",
                      "Facials","Waxing","Manicures and pedicures","Lash extensions",
                      "Spray tanning","Bridal hair and makeup","Spa packages","Spa memberships"]}


def _price_offer(name, price):
    """Turn a menu price string into a schema.org Offer, or None if it is not a price."""
    t = html.unescape(price).replace(",", "").strip()
    m = re.match(r"^\$(\d+(?:\.\d+)?)(\+?)$", t)
    if m:
        amt = float(m.group(1)); amt = int(amt) if amt.is_integer() else amt
        if m.group(2):   # "$70+" = starting price
            return {"@type":"Offer","itemOffered":{"@type":"Service","name":name},
                    "priceSpecification":{"@type":"PriceSpecification","minPrice":amt,"priceCurrency":"USD"},
                    "availability":"https://schema.org/InStock"}
        return {"@type":"Offer","itemOffered":{"@type":"Service","name":name},
                "price":amt,"priceCurrency":"USD","availability":"https://schema.org/InStock"}
    if t.lower() == "complimentary":
        return {"@type":"Offer","itemOffered":{"@type":"Service","name":name},
                "price":0,"priceCurrency":"USD"}
    return None


def offer_catalog(groups, service):
    cats=[]
    for title,rows in groups:
        items=[o for o in (_price_offer(html.unescape(r[0]), r[1]) for r in rows) if o]
        if items:
            cats.append({"@type":"OfferCatalog","name":html.unescape(title),"itemListElement":items})
    return {"@type":"OfferCatalog","name":f"{service} menu","itemListElement":cats} if cats else None


def page_schema(p):
    url = DOMAIN+"/"+(p["path"]+"/" if p["path"] else "")
    g=[biz_node(),
       {"@type":"WebSite","@id":DOMAIN+"/#website","url":DOMAIN+"/","name":NAME,
        "publisher":{"@id":DOMAIN+"/#business"},"inLanguage":"en-US"},
       {"@type":"WebPage","@id":url+"#webpage","url":url,"name":p["title"],
        "description":p["desc"],"isPartOf":{"@id":DOMAIN+"/#website"},
        "about":{"@id":DOMAIN+"/#business"},"inLanguage":"en-US",
        "primaryImageOfPage":DOMAIN+OG_IMG.get(p["path"],OG_IMG[""])}]
    crumbs=[{"@type":"ListItem","position":1,"name":"Home","item":DOMAIN+"/"}]
    if p.get("parent"):
        pp = next(x for x in PAGES if x["path"]==p["parent"])
        crumbs.append({"@type":"ListItem","position":2,"name":pp["nav"],"item":f'{DOMAIN}/{pp["path"]}/'})
    if p["path"]:
        crumbs.append({"@type":"ListItem","position":len(crumbs)+1,"name":p["nav"],
                       "item":f'{DOMAIN}/{p["path"]}/'})
    g.append({"@type":"BreadcrumbList","itemListElement":crumbs})
    if p.get("service"):
        svc={"@type":"Service","@id":url+"#service","name":p["service"],"serviceType":p["service"],
             "url":url,"areaServed":[{"@type":"City","name":f"{t}, NY"} for t in NEARBY],
             "provider":{"@id":DOMAIN+"/#business"}}
        cat = offer_catalog(p["groups"], p["service"]) if p.get("groups") else None
        if cat: svc["hasOfferCatalog"]=cat
        g.append(svc)
    if p.get("persons"):
        for nm,rl,img in p["persons"]:
            node={"@type":"Person","name":nm,"jobTitle":rl,"worksFor":{"@id":DOMAIN+"/#business"},
                  "url":f"{DOMAIN}/team/{slugify(nm)}/"}
            if img: node["image"]=DOMAIN+"/images/team/"+img
            g.append(node)
    if p.get("person"):
        ps=p["person"]
        node={"@type":"Person","@id":url+"#person","name":ps["name"],"jobTitle":ps["role"],
              "description":ps["desc"],"url":url,"worksFor":{"@id":DOMAIN+"/#business"},
              "workLocation":{"@type":"Place","address":{"@type":"PostalAddress","streetAddress":STREET,
                 "addressLocality":CITY,"addressRegion":STATE,"postalCode":ZIP,"addressCountry":"US"}},
              "knowsAbout":ps["knows"],"telephone":PHONE_TEL}
        if ps.get("img"): node["image"]=DOMAIN+"/images/team/"+ps["img"]
        if ps.get("credential"):
            node["hasCredential"]={"@type":"EducationalOccupationalCredential","credentialCategory":"license","name":ps["credential"]}
        g.append(node)
        g[2]["about"]={"@id":url+"#person"}   # WebPage is about the person
        g[2]["mainEntity"]={"@id":url+"#person"}
    if p.get("faq"):
        g.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,
            "acceptedAnswer":{"@type":"Answer","text":a}} for q,a in p["faq"]]})
    return json.dumps({"@context":"https://schema.org","@graph":g},indent=1)

# ------------------------------------------------------------------ shell
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="website">
<meta property="og:image" content="{ogimg}">
<meta property="og:image:alt" content="Omorfia Salon &amp; Day Spa, Poughkeepsie NY">
<meta property="og:site_name" content="Omorfia Salon &amp; Day Spa">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{ogimg}">
<meta name="geo.region" content="US-NY">
<meta name="geo.placename" content="Poughkeepsie">
<meta name="geo.position" content="{lat};{lng}">
<meta name="ICBM" content="{lat}, {lng}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="image" href="/images/slides/s08.webp" fetchpriority="high">
<link rel="preconnect" href="https://static.joinboulevard.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Infant:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Jost:wght@300;400;500&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Cormorant+Infant:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Jost:wght@300;400;500&display=swap" rel="stylesheet"></noscript>
<link rel="stylesheet" href="/styles.css">
<script type="application/ld+json">
{schema}
</script>
<!-- Boulevard Self-Booking overlay -->
<script>
(function (a) {{
  var b = {{ businessId: '549d4738-8602-4141-b4b4-f1b11bb4f2a4' }};
  var c = a.createElement('script'); var d = a.querySelector('script');
  c.src = 'https://static.joinboulevard.com/injector.min.js'; c.async = true;
  c.onload = function () {{ blvd.init(b); window.__blvdReady = true; }};
  d.parentNode.insertBefore(c, d);
}})(document);
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <a class="sh-word" href="/">OMORFIA</a>
  <input type="checkbox" id="navtoggle" class="navtoggle" aria-label="Open menu">
  <label for="navtoggle" class="burger"><span></span><span></span><span></span></label>
  <nav class="sh-nav" aria-label="Main">
    <div class="dd">
      <a href="/hair/">Salon <svg class="chev" width="11" height="7" viewBox="0 0 11 7" fill="none" aria-hidden="true"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.4" fill="none"/></svg></a>
      <div class="dd-menu">
        <a href="/hair/">Hair</a>
        <a href="/balayage/">Balayage</a>
        <a href="/hair-extensions/">Hair Extensions</a>
        <a href="/keratin-treatment/">Keratin Smoothing</a>
        <a href="/japanese-head-spa/">Japanese Head Spa</a>
        <a href="/lashes-brows/">Lashes &amp; Brows</a>
        <a href="/microblading/">Microblading</a>
        <a href="/makeup/">Makeup</a>
        <a href="/prom-hair-and-makeup/">Prom</a>
        <a href="/wedding/">Wedding &amp; Bridal</a>
      </div>
    </div>
    <div class="dd">
      <a href="/massage/">Spa <svg class="chev" width="11" height="7" viewBox="0 0 11 7" fill="none" aria-hidden="true"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.4" fill="none"/></svg></a>
      <div class="dd-menu">
        <a href="/massage/">Massage</a>
        <a href="/couples-massage/">Couples Massage</a>
        <a href="/deep-tissue-massage/">Deep Tissue</a>
        <a href="/prenatal-massage/">Prenatal Massage</a>
        <a href="/facials/">Facials &amp; Esthetics</a>
        <a href="/brazilian-wax/">Waxing</a>
        <a href="/nails/">Nails</a>
        <a href="/tanning/">Tanning</a>
        <a href="https://omomedspa.com" target="_blank" rel="noopener">Med Spa</a>
      </div>
    </div>
    <div class="dd">
      <a href="/packages/">Packages <svg class="chev" width="11" height="7" viewBox="0 0 11 7" fill="none" aria-hidden="true"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.4" fill="none"/></svg></a>
      <div class="dd-menu">
        <a href="/packages/">Packages</a>
        <a href="/memberships/">Memberships</a>
        <a href="/menu/">Services &amp; Prices</a>
        <a href="/gift-cards/">Gift Cards</a>
        <a href="/specials/">New Guest Offer</a>
      </div>
    </div>
    <div class="dd">
      <a href="/about/">About <svg class="chev" width="11" height="7" viewBox="0 0 11 7" fill="none" aria-hidden="true"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.4" fill="none"/></svg></a>
      <div class="dd-menu">
        <a href="/about/">Our Story</a>
        <a href="/team/">Meet the Team</a>
        <a href="/reviews/">Reviews</a>
        <a href="/hudson-valley/">Areas We Serve</a>
        <a href="/contact/">Contact &amp; Hours</a>
      </div>
    </div>
    <div class="dd">
      <a href="https://kyriacoubeauty.com" rel="noopener">Kyriacou <svg class="chev" width="11" height="7" viewBox="0 0 11 7" fill="none" aria-hidden="true"><path d="M1 1l4.5 4.5L10 1" stroke="currentColor" stroke-width="1.4" fill="none"/></svg></a>
      <div class="dd-menu">
        <a href="https://kyriacoubeauty.com" rel="noopener">Kyriacou Cosmetics</a>
        <a href="https://omomedspa.com" target="_blank" rel="noopener">OMO Med Spa</a>
        <a href="https://kyriacoubeauty.com" rel="noopener">Kyriacou Beauty Group</a>
      </div>
    </div>
    <a href="/contact/">Location</a>
  </nav>
  <div class="sh-actions">
    <a class="sh-book" href="{book}">Book</a>
    <a class="sh-gift" href="/gift-cards/">Gift Cards</a>
  </div>
</header>
<a class="book-float" href="{book}">Book Appointment</a>
<main id="main">
"""

FOOT = """</main>
<section class="cta-band">
  <p class="cta-greek" aria-hidden="true">&omicron;&mu;&omicron;&rho;&phi;&iota;&#940;</p>
  <h2>Ready when you are.</h2>
  <p class="cta-sub">Book online in under a minute, or call the front desk.</p>
  <div class="cta-actions">
    <a class="btn btn-primary" href="{book}">Book Appointment</a>
    <a class="btn btn-ghost" href="tel:{tel}">{phone}</a>
  </div>
</section>
<footer class="foot">
  <div class="foot-grid">
    <div>
      <p class="foot-brand">OMORFIA</p>
      <p class="foot-def"><em>omorfi&aacute;</em> &mdash; Greek, &ldquo;beauty&rdquo;</p>
      <p class="foot-addr">{street}<br>{city}, {state} {zip}<br><a href="tel:{tel}">{phone}</a></p>
    </div>
    <div>
      <p class="foot-h">Hours</p>
      <p class="foot-hours">Open 7 Days a Week<br>9:00 AM &ndash; 8:00 PM</p>
    </div>
    <div>
      <p class="foot-h">Salon &amp; Spa</p>
      <p><a href="/hair/">Hair</a> &middot; <a href="/nails/">Nails</a> &middot; <a href="/massage/">Massage</a><br>
      <a href="/facials/">Facials</a> &middot; <a href="/tanning/">Tanning</a> &middot; <a href="/makeup/">Makeup</a><br>
      <a href="/wedding/">Wedding &amp; Bridal</a> &middot; <a href="/lashes-brows/">Lashes &amp; Brows</a></p>
    </div>
    <div>
      <p class="foot-h">Explore</p>
      <p><a href="/packages/">Packages</a> &middot; <a href="/memberships/">Memberships</a><br>
      <a href="/specials/">Specials</a> &middot; <a href="/gift-cards/">Gift Cards</a><br>
      <a href="/team/">Team</a> &middot; <a href="/reviews/">Reviews</a> &middot; <a href="/contact/">Contact</a><br>
      <a href="/menu/">Services &amp; Prices</a> &middot; <a href="/hudson-valley/">Areas We Serve</a></p>
    </div>
    <div>
      <p class="foot-h">Popular</p>
      <p><a href="/japanese-head-spa/">Japanese Head Spa</a> &middot; <a href="/couples-massage/">Couples Massage</a><br>
      <a href="/deep-tissue-massage/">Deep Tissue</a> &middot; <a href="/prenatal-massage/">Prenatal Massage</a><br>
      <a href="/balayage/">Balayage</a> &middot; <a href="/hair-extensions/">Extensions</a> &middot; <a href="/keratin-treatment/">Keratin</a><br>
      <a href="/microblading/">Microblading</a> &middot; <a href="/brazilian-wax/">Waxing</a> &middot; <a href="/prom-hair-and-makeup/">Prom</a></p>
    </div>
    <div>
      <p class="foot-h">Family</p>
      <p><a href="https://kyriacoubeauty.com" rel="noopener">Kyriacou Beauty Group</a><br>
      <a href="https://www.instagram.com/omorfiadayspa/" rel="noopener">Instagram</a></p>
    </div>
  </div>
  <p class="foot-legal">&copy; 2026 Omorfia Salon &amp; Day Spa &middot; A Kyriacou Beauty Group company &middot; {city}, {state}</p>
</footer>
</body>
</html>
"""

def faq_html(faq):
    if not faq: return ""
    items="\n".join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q,a in faq)
    return f'<section class="wrap faq"><p class="eyebrow">Questions</p><h2>Good to know</h2>{items}</section>'

def svc_list(items):
    rows="\n".join(f'<li><span class="svc-name">{html.escape(n)}</span><span class="svc-desc">{html.escape(d)}</span></li>' for n,d in items)
    return f'<ul class="svc-list">{rows}</ul>'

def _vslug(name):
    t = name
    for a,b in (("&amp;","and"),("&rsquo;",""),("&ndash;","-"),("&ecirc;","e"),("&nbsp;"," ")):
        t = t.replace(a,b)
    t = re.sub(r"[^a-z0-9]+","-", t.lower()).strip("-")
    return t

def _find_video(page_slug, item_name):
    for cand in (_vslug(item_name), page_slug):
        for ext in ("mp4","webm"):
            if os.path.exists(f"site/videos/{cand}.{ext}"):
                return f"/videos/{cand}.{ext}"
    return None

MODAL_JS = """<script>
(function(){
  if(window.__omModal)return; window.__omModal=1;
  function open(id){var m=document.getElementById(id);if(!m)return;m.hidden=false;document.documentElement.classList.add('op-lock');
    var v=m.querySelector('video');if(v){v.currentTime=0;v.play().catch(function(){});}}
  function closeAll(){document.querySelectorAll('.tmodal').forEach(function(m){m.hidden=true;var v=m.querySelector('video');if(v)v.pause();});document.documentElement.classList.remove('op-lock');}
  document.addEventListener('click',function(e){
    var c=e.target.closest('[data-open]');
    if(c){open(c.getAttribute('data-open'));return;}
    if(e.target.closest('[data-tclose]'))closeAll();
  });
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape')closeAll();
    if(e.key==='Enter'||e.key===' '){
      var c=document.activeElement;
      if(c&&c.hasAttribute&&c.hasAttribute('data-open')){e.preventDefault();open(c.getAttribute('data-open'));}
    }
  });
})();
</script>"""

def menu_html(groups, page_slug):
    out=[]; modals=[]; i=0
    for title,rows in groups:
        lis=[]
        for r in rows:
            n,p,d = r[0],r[1],r[2]
            m = r[3] if len(r)>3 else None
            longd = r[4] if len(r)>4 and r[4] else d
            mid = f"sm-{page_slug}-{i}"; i+=1
            desc = f'<p class="pl-desc">{d}</p>' if d else ''
            if m:
                desc += (f'<p class="pl-member"><span class="pl-member-tag">Members</span> {m} '
                         f'<span class="pl-member-sep">&middot;</span> <a href="/memberships/">See member club</a></p>')
            lis.append(f'<li role="button" tabindex="0" data-open="{mid}" aria-haspopup="dialog">'
                       f'<div class="pl-row"><span class="pl-name">{n}</span>'
                       f'<span class="pl-dots" aria-hidden="true"></span>'
                       f'<span class="pl-price">{p}</span></div>{desc}</li>')
            vid = _find_video(page_slug, n)
            if vid:
                media = f'<div class="tm-media"><video src="{vid}" autoplay muted loop playsinline preload="metadata"></video></div>'
                card_cls = "tm-card"
            else:
                media = ""
                card_cls = "tm-card tm-solo"
            modals.append(
              f'<div class="tmodal" id="{mid}" role="dialog" aria-modal="true" aria-label="{n}" hidden>'
              f'<div class="tm-back" data-tclose></div>'
              f'<div class="{card_cls}"><button class="tm-x" data-tclose aria-label="Close">&times;</button>'
              f'{media}'
              f'<div class="tm-info"><p class="eyebrow">{p}{(" &middot; Members "+m) if m else ""}</p><h3>{n}</h3>'
              f'<p class="tm-bio">{longd}</p>'
              + (f'<p class="tm-member">Members pay <strong>{m}</strong> for this service &mdash; <a href="/memberships/">join the Omorfia Member Club</a>.</p>' if m else '')
              + f'<a class="btn btn-primary" href="{{book}}">Book This Service</a></div>'
              f'</div></div>')
        out.append(f'<div class="menu-group"><h3>{title}</h3><ul class="price-list">{"".join(lis)}</ul></div>')
    return '<div class="menu-grid">'+"".join(out)+'</div>' + "".join(modals) + MODAL_JS

def service_video(slug, nav):
    for ext in ("mp4","webm"):
        p = f"site/videos/{slug}.{ext}"
        if os.path.exists(p):
            return f"""
<section class="wrap vid-wrap">
  <p class="eyebrow">See it for yourself</p>
  <h2>{nav}, in motion</h2>
  <video class="svc-video" autoplay muted loop playsinline preload="metadata" src="/videos/{slug}.{ext}"></video>
</section>"""
    return ""

RELATED = {
 "hair":    [("/balayage/","Balayage"),("/hair-extensions/","Hair Extensions"),("/keratin-treatment/","Keratin Smoothing"),("/japanese-head-spa/","Japanese Head Spa"),("/prom-hair-and-makeup/","Prom Hair &amp; Makeup"),("/wedding/","Bridal Hair")],
 "massage": [("/couples-massage/","Couples Massage"),("/deep-tissue-massage/","Deep Tissue Massage"),("/prenatal-massage/","Prenatal Massage"),("/packages/","Spa Packages"),("/memberships/","Massage Club")],
 "facials": [("/brazilian-wax/","Brazilian &amp; Body Waxing"),("/japanese-head-spa/","Japanese Head Spa Facial"),("/packages/","Spa Packages"),("/memberships/","Facial Club")],
 "nails":   [("/packages/","Spa Packages"),("/memberships/","Mani &amp; Pedi Club"),("/prom-hair-and-makeup/","Prom Nails")],
 "lashes-brows": [("/microblading/","Microblading"),("/makeup/","Makeup"),("/wedding/","Bridal Lashes")],
 "makeup":  [("/prom-hair-and-makeup/","Prom Hair &amp; Makeup"),("/wedding/","Wedding &amp; Bridal"),("/lashes-brows/","Lash Extensions")],
 "tanning": [("/prom-hair-and-makeup/","Prom Glow"),("/wedding/","Bridal"),("/packages/","Spa Packages")],
}
def related_html(slug):
    links = RELATED.get(slug)
    if not links: return ""
    items = " &middot; ".join(f'<a href="{u}">{t}</a>' for u,t in links)
    return f'<section class="wrap related"><p class="eyebrow">Explore</p><h2>You might also be looking for</h2><p class="related-links">{items}</p></section>'

def service_page(slug,nav,service,title,desc,h1,intro,groups,faq,img,note=None,kw=None,reviews=None,team=None):
    kw = kw or f"{service} in Poughkeepsie, NY"
    rv = ""
    if reviews:
        rv = (f'<section class="wrap reviews-wrap"><p class="eyebrow">Google reviews</p>'
              f'<h2>What guests say about {nav.lower()} at Omorfia</h2>{review_cards(reviews)}'
              f'<p class="menu-note"><a class="btn-link" href="/reviews/">Read more reviews &rarr;</a> &middot; '
              f'<a class="btn-link" href="https://www.google.com/maps/place/?q=place_id:{PLACE_ID}" rel="noopener">See all on Google &rarr;</a></p></section>')
    tm = ""
    if team:
        tm = (f'<section class="wrap team-links"><p class="eyebrow">{team[0]}</p><h2>{team[1]}</h2>'
              f'<p class="related-links">' + " &middot; ".join(f'<a href="/team/{slugify(n)}/">{n.split()[0]}</a> <span class="tl-role">({r})</span>' for n,r in team[2]) +
              f'</p><p class="menu-note"><a class="btn-link" href="/team/">Meet the whole team &rarr;</a></p></section>')
    body=f"""
<section class="page-hero has-photo" style="background-image:url('{img}')">
  <div class="ph-inner">
    <h1 class="eyebrow">{kw}</h1>
    <p class="ph-title">{h1}</p>
    <p class="lead">{intro}</p>
    <a class="btn btn-primary" href="{{book}}">Book {nav}</a>
  </div>
</section>
<section class="wrap menu-wrap">
  <p class="eyebrow">The menu</p>
  <h2>Services &amp; pricing</h2>
  {menu_html(groups, slug)}
  {('<p class="menu-note brand-note">'+note+'</p>') if note else ''}
  <p class="menu-note">Prices are starting points and may vary with length, density, and service time &mdash; your provider confirms an exact quote before beginning. Book online or call <a href="tel:{PHONE_TEL}">{PHONE}</a>.</p>
</section>
{tm}
{rv}
{faq_html(faq)}
{related_html(slug)}
"""
    return dict(path=slug,nav=nav,service=service,title=title,desc=desc,body=body,faq=faq,faq_done=True,groups=groups)


def topic_page(slug,nav,service,parent,title,desc,kw,tagline,intro,sections,groups,faq,img,related,cta=None):
    """Long-tail landing page: hero + editorial sections + pricing (menu rows) + FAQ + related links."""
    prose = "".join(f'<h3>{h}</h3>' + "".join(f'<p>{para}</p>' for para in ps) for h,ps in sections)
    rel = " &middot; ".join(f'<a href="{u}">{t}</a>' for u,t in related)
    body=f"""
<section class="page-hero has-photo" style="background-image:url('{img}')">
  <div class="ph-inner">
    <h1 class="eyebrow">{kw}</h1>
    <p class="ph-title">{tagline}</p>
    <p class="lead">{intro}</p>
    <a class="btn btn-primary" href="{{book}}">{cta or ("Book " + nav)}</a>
  </div>
</section>
<section class="wrap prose-wrap">
  <div class="prose">{prose}</div>
</section>
<section class="wrap menu-wrap">
  <p class="eyebrow">Pricing</p>
  <h2>{nav} pricing</h2>
  {menu_html(groups, slug)}
  <p class="menu-note">Prices are starting points and may vary with length, density, and service time &mdash; your provider confirms an exact quote before beginning. Book online or call <a href="tel:{PHONE_TEL}">{PHONE}</a>.</p>
</section>
{faq_html(faq)}
<section class="wrap related"><p class="eyebrow">Explore</p><h2>You might also be looking for</h2><p class="related-links">{rel}</p></section>
"""
    return dict(path=slug,nav=nav,service=service,parent=parent,title=title,desc=desc,body=body,faq=faq,faq_done=True,groups=groups)

REVIEWS = [
 ("This was my first visit to Omorfia for a massage, and I couldn&rsquo;t have asked for a better experience. Debbie was absolutely amazing from start to finish. Her hands are truly magical &mdash; every touch was both deeply therapeutic and incredibly relaxing.","Massage &middot; Google review"),
 ("Christie was fabulous &mdash; she listened to me and my hair was done exactly like I wanted. She also did my pedicure and that was excellent as well. It is such a welcoming, lovely salon.","Hair &amp; Nails &middot; Google review"),
 ("My mom and I went today and both got pedicures from Christie and Patsy! They&rsquo;re amazing and we left feeling like celebrities! They took their time and I&rsquo;ve never been happier. Will definitely be back again!","Pedicures &middot; Google review"),
 ("She is incredibly professional, attentive, and truly skilled at what she does. Her massages are not only relaxing but also therapeutic &mdash; she knows exactly how to target areas of tension and provide lasting relief.","Massage with Debbie &middot; Google review"),
 ("Where do I start? Omorfia Spa is a hidden gem that I&rsquo;m so excited I found. I couldn&rsquo;t believe they were open on a SUNDAY for an appointment! I was able to book online without a problem and was greeted by Debby when I arrived&hellip; She has incorporated the use of crystals with my deep tissue body work and the difference with my mind and body being grounding is noticeable. The massage room is huge with ambiance that is perfect for peace.","Cassandra T. &middot; Google Review"),
 ("I&rsquo;ve been going to Christie at Omorfia Beauty regularly for my cut and color, and she is absolutely great! She consistently delivers perfect results, listens to exactly what I want, and makes every visit wonderful. Highly recommend!","A. Hopkins &middot; Google Review"),
 ("Georgia and Nevaeh were great! They took me in as a walk in and Georgia did a beautiful job!","Paige I. &middot; Google Review"),
 ("My full body massage with Debbie today was both therapeutic and relaxing at the same time. She targeted my tight muscles with great skill and left me feeling completely refreshed. I highly recommend a session with her.","Google Review &middot; Massage"),
 ("I really appreciate OMORFIA! Sandy does a great pedicure and mani &mdash; my smoky lavender pedicure looks so summery! Georgia is a delightful hair expert. I had my waist length hair blown out for a special date night. My hair has never looked and felt so lush&hellip; They are so welcoming and attentive upon arrival and departure.","Mia M. &middot; Google Review"),
 ("I get nail services done and it&rsquo;s amazing! I recently joined the monthly membership and it&rsquo;s great. Highly recommend! Sandy is the best!","Jacqueline C. &middot; Google Review"),
 ("Patsy is absolutely the best for your eyebrows. She will take care of them like they are her own!!!! I haven&rsquo;t had eyebrows in years and I have to tell you how much I love them. I actually cried when I looked in the mirror!!!! I had my doubts. I was scared, but I&rsquo;m so glad I went. Thank you, Patsy.","Debbie S. &middot; Google Review"),
 ("What a beautiful experience. This was my first hot stone combo massage and it was incredible&hellip; Between the stones and Debbie&rsquo;s skill, I felt my muscles relaxing and elongating. Debbie is very in tune and intuitive and this was absolutely one of my favorite massage experiences. My body feels soft and relaxed, but also energized. Highly recommend!","Google Review &middot; Hot Stone Massage"),
 ("Got a curly cut from Hailey! Excellent job, very efficient, awesome shape and provided some education on how to maintain my hair&rsquo;s health!","Quelania J. &middot; Google Review"),
 ("I go to Erin here for my touch ups and color services. She&rsquo;s always going above and beyond to make sure I leave happy :) she&rsquo;s so trendy and chic! I can truly say that every time I go here, I leave with my expectations blown out of the water. Erin truly knows my hair by now too and that makes me so comfortable knowing she gets me.","Mitchie &middot; Google Review"),
 ("Erin was my hair stylist, and she was so kind and sweet. We chatted throughout the appointment and I had a lot of fun with her. My hair turned out so great, I&rsquo;m so happy with it! If you come to Omorfia, I hope you&rsquo;re lucky enough to get Erin as your hair stylist.","Kristina L. &middot; Google Review"),
 ("Wonderful massage by Debbie who is very experienced. Has a 90 minute deep tissue. Staff is very friendly and they offer a lot of other services. I will be back!!","Google Review &middot; Deep Tissue Massage")
]
MASSAGE_REVIEWS = [r for r in REVIEWS if "massage" in (r[0]+r[1]).lower()]
HAIR_REVIEWS    = [r for r in REVIEWS if re.search(r'hair|cut|color|blow', (r[0]+r[1]), re.I) and "massage" not in r[0].lower()]
def person_reviews(first):
    return [r for r in REVIEWS if re.search(r'\b'+re.escape(first)+r'\b', r[0], re.I)]

def review_cards(rs):
    slides = "".join(
      f'<figure class="rvl">'
      f'<div class="rvl-stars" aria-label="Rated 5 out of 5">&#9733;&#9733;&#9733;&#9733;&#9733;</div>'
      f'<blockquote>&ldquo;{t}&rdquo;</blockquote>'
      f'<hr class="rvl-rule">'
      f'<figcaption>{w}</figcaption></figure>'
      for t,w in rs)
    return ('<div class="rvl-wrap">'
      '<div class="rvl-scroll">'+slides+'</div>'
      '</div>'
      """<script>
(function(){
  document.querySelectorAll('.rvl-wrap').forEach(function(w){
    if(w.dataset.rvl)return; w.dataset.rvl='1';
    var sc=w.querySelector('.rvl-scroll');
    var n=sc.children.length; if(n<2)return;
    if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    var i=0,paused=false;
    sc.addEventListener('pointerenter',function(){paused=true;});
    sc.addEventListener('pointerleave',function(){paused=false;});
    sc.addEventListener('touchstart',function(){paused=true;},{passive:true});
    sc.addEventListener('touchend',function(){setTimeout(function(){paused=false;},9000);},{passive:true});
    sc.addEventListener('scroll',function(){var w2=sc.clientWidth||1;i=Math.round(sc.scrollLeft/w2);},{passive:true});
    setInterval(function(){
      if(paused||document.hidden)return;
      i=(i+1)%n;
      sc.scrollTo({left:i*sc.clientWidth,behavior:'smooth'});
    },6000);
  });
})();
</script>""")

PAGES=[]

# ---------------------------------------------------------------- home
PAGES.append(dict(path="",nav="Home",
 title="Day Spa in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 desc="Omorfia is a full-service salon and day spa in Poughkeepsie, NY — hair, nails, massage, facials, tanning, makeup and bridal. Open 7 days a week, including Sundays. Book online or call (845) 694-4952.",
 body=f"""
<section class="hero">
  <div class="hero-slides-layer" id="heroSlides" aria-hidden="true"></div>
  <div class="hero-veil" aria-hidden="true"></div>
  <p class="hero-def"><em>omorfi&aacute;</em> &mdash; Greek, &ldquo;beauty&rdquo;</p>
  <p class="hero-brand">OMORFIA</p>
  <div class="rule" aria-hidden="true"></div>
  <h1 class="hero-sub">Salon &amp; Day Spa &nbsp;&middot;&nbsp; Poughkeepsie, New York</h1>
  <p class="hero-tag">Where Beauty Meets Relaxation</p>
  <p class="hero-open">Open 7 Days a Week &middot; <span class="hero-star">&#9733;</span> 4.9 on Google</p>
  <div class="primary-row"><a class="btn btn-primary" href="{{book}}">Book Appointment</a></div>
  <div class="secondary-row">
    <a class="btn-link" href="/packages/">Spa Packages</a><span class="dot">&middot;</span>
    <a class="btn-link" href="#services">Explore Services</a><span class="dot">&middot;</span>
    <a class="btn-link" href="/gift-cards/">Gift Cards</a>
  </div>
</section>
<div class="offer-pop" id="offerPop" role="dialog" aria-modal="true" aria-label="First-time guest offer" hidden>
  <div class="op-backdrop" data-close></div>
  <div class="op-card">
    <button class="op-x" data-close aria-label="Close">&times;</button>
    <div class="op-top">
      <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="3" y="8" width="18" height="4"/><rect x="5" y="12" width="14" height="9"/><line x1="12" y1="8" x2="12" y2="21"/><path d="M12 8c-2.5 0-4.5-1.2-4.5-2.8C7.5 3.9 8.6 3 9.9 3c1.7 0 2.1 2.4 2.1 5zm0 0c2.5 0 4.5-1.2 4.5-2.8C16.5 3.9 15.4 3 14.1 3 12.4 3 12 5.4 12 8z"/></svg>
      <p class="op-eyebrow">First-Time Guest Offer</p>
      <p class="op-big">$15 OFF</p>
      <p class="op-sub">your first visit</p>
    </div>
    <div class="op-bottom">
      <p>Book your first appointment and mention this offer at checkout &mdash; $15 off, no strings attached.</p>
      <a class="btn btn-primary op-cta" href="{{book}}">Book My First Visit</a>
      <button class="op-no" data-close>No thanks</button>
    </div>
  </div>
</div>
<script>
(function(){{
  var pop=document.getElementById('offerPop');if(!pop)return;
  var KEY='omorfiaOfferSeen';
  function seen(){{try{{return sessionStorage.getItem(KEY)==='1';}}catch(e){{return false;}}}}
  function mark(){{try{{sessionStorage.setItem(KEY,'1');}}catch(e){{}}}}
  function close(){{pop.hidden=true;document.documentElement.classList.remove('op-lock');mark();}}
  if(seen())return;
  setTimeout(function(){{pop.hidden=false;document.documentElement.classList.add('op-lock');}},1400);
  pop.addEventListener('click',function(e){{if(e.target.closest('[data-close]'))close();}});
  document.addEventListener('keydown',function(e){{if(e.key==='Escape'&&!pop.hidden)close();}});
}})();
</script>
<script>
(function(){{
  var imgs=["/images/slides/s01.jpg","/images/slides/s02.jpg","/images/slides/s03.jpg","/images/slides/s04.jpg","/images/slides/s05.jpg","/images/slides/s06.jpg","/images/slides/s07.jpg","/images/slides/s08.jpg","/images/slides/s09.jpg","/images/slides/s10.jpg","/images/slides/s11.jpg","/images/slides/s12.jpg","/images/slides/s13.jpg","/images/slides/s14.jpg","/images/slides/s15.jpg","/images/slides/s16.jpg","/images/slides/s17.jpg","/images/slides/s18.jpg","/images/slides/s19.jpg","/images/slides/s20.jpg"];
  imgs.splice(imgs.indexOf("/images/slides/s08.jpg"),1);
  for(var i=imgs.length-1;i>0;i--){{var j=Math.floor(Math.random()*(i+1));var t=imgs[i];imgs[i]=imgs[j];imgs[j]=t;}}
  imgs.unshift("/images/slides/s08.jpg");
  var wrap=document.getElementById('heroSlides');if(!wrap)return;
  var a=document.createElement('div'),b=document.createElement('div');
  a.className='hslide on';b.className='hslide';
  wrap.appendChild(a);wrap.appendChild(b);
  a.style.backgroundImage="url('"+imgs[0]+"')";
  if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var idx=0,front=a,back=b;
  setInterval(function(){{
    idx=(idx+1)%imgs.length;
    var im=new Image();
    im.onload=function(){{
      back.style.backgroundImage="url('"+imgs[idx]+"')";
      back.classList.add('on');front.classList.remove('on');
      var t=front;front=back;back=t;
    }};
    im.src=imgs[idx];
  }},5200);
}})();
</script>
<section class="wrap welcome">
  <p class="eyebrow">Welcome</p>
  <h2>The Hudson Valley&rsquo;s full-service salon &amp; day spa</h2>
  <p class="lead">We&rsquo;re glad you&rsquo;re here. From precision cuts, dimensional color and bridal beauty to massage, facials, nails and a sunless glow, Omorfia brings every service under one roof in Poughkeepsie &mdash; delivered by hand-picked providers with a thoughtful approach to every guest.</p>
  <div class="welcome-ctas">
    <a class="btn btn-outline" href="#services">Explore Services</a>
    <a class="btn btn-outline" href="/specials/">New Guest Offer</a>
    <a class="btn btn-outline" href="/gift-cards/">Gift Cards</a>
  </div>
</section>
<section class="photo-grid-sec" id="services">
  <div class="wrap-wide">
    <p class="eyebrow">Salon &amp; Spa</p>
    <h2>Everything under one appointment</h2>
    <div class="pgrid">
      <a class="pcard" href="/hair/"><img class="pimg" src="/images/home-hair.jpg" alt="Hair salon in Poughkeepsie &mdash; cuts, color and balayage at Omorfia" loading="lazy" width="1200" height="900"><span class="pc-n">Hair</span><span class="pc-d">Cuts, color, balayage &amp; blowouts</span></a>
      <a class="pcard" href="/nails/"><img class="pimg" src="/images/home-nails.jpg" alt="Nail salon in Poughkeepsie &mdash; manicures, pedicures and gel at Omorfia" loading="lazy" width="1200" height="900"><span class="pc-n">Nails</span><span class="pc-d">Manicures, pedicures &amp; gel</span></a>
      <a class="pcard" href="/massage/"><img class="pimg" src="/images/home-massage.jpg" alt="Massage room at Omorfia Day Spa in Poughkeepsie" loading="lazy" width="1200" height="900"><span class="pc-n">Massage</span><span class="pc-d">Swedish, deep tissue &amp; couples</span></a>
      <a class="pcard" href="/facials/"><img class="pimg" src="/images/home-facials.jpg" alt="Facial treatment at Omorfia Day Spa in Poughkeepsie" loading="lazy" width="1200" height="900"><span class="pc-n">Facials</span><span class="pc-d">Esthetics, peels &amp; skin care</span></a>
      <a class="pcard" href="/tanning/"><img class="pimg" src="/images/home-tanning.jpg" alt="Spray tanning at Omorfia in Poughkeepsie" loading="lazy" width="1200" height="900"><span class="pc-n">Tanning</span><span class="pc-d">A natural sunless glow</span></a>
      <a class="pcard" href="/makeup/"><img class="pimg" src="/images/home-makeup.jpg" alt="Makeup artistry at Omorfia Salon in Poughkeepsie" loading="lazy" width="1200" height="900"><span class="pc-n">Makeup</span><span class="pc-d">Events, weddings &amp; lessons</span></a>
    </div>
  </div>
</section>
<section class="feature" style="background-image:linear-gradient(rgba(11,11,11,.62),rgba(11,11,11,.62)),url('/images/slides/s08.jpg')">
  <div class="feat-inner">
    <p class="eyebrow inv">Beauty, wellness &amp; expertise under one roof</p>
    <h2>A day spa, not a chain</h2>
    <p>Locally owned and operated on Dutchess Turnpike, Omorfia was built to be a safe, warm space where Poughkeepsie comes to slow down &mdash; hand-picked providers, deliberate product lines, and a front desk that knows your name by the second visit. And we&rsquo;re open seven days a week &mdash; because your schedule doesn&rsquo;t take Sundays off.</p>
    <a class="btn btn-primary" href="/about/">Our Story</a>
  </div>
</section>
<section class="wrap reviews-sec">
  <p class="eyebrow">Loved by the Hudson Valley</p>
  <h2>What guests say</h2>
  {review_cards(REVIEWS)}
  <p class="center"><a class="btn-link" href="/reviews/">Read more reviews &rarr;</a></p>
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">Make it a ritual</p>
    <h2>Memberships</h2>
    <p>A membership banks your favorite service every month at member pricing. It&rsquo;s the difference between treating yourself once and actually taking care of yourself.</p>
    <p><a class="btn-link" href="/memberships/">See memberships &rarr;</a></p>
  </div>
  <div>
    <p class="eyebrow">Design your day</p>
    <h2>Spa packages</h2>
    <p>Bundle massage, facial, nails and hair into one appointment at a saving over &agrave; la carte &mdash; arrive once, hand over your afternoon, leave new.</p>
    <p><a class="btn-link" href="/packages/">See packages &rarr;</a></p>
  </div>
</section>
<section class="gift-band">
  <div class="wrap gift-inner">
    <div>
      <p class="eyebrow">The easiest gift in the Hudson Valley</p>
      <h2>Give an Omorfia day</h2>
      <p>Gift cards work across every service &mdash; hair, spa, packages, all of it.</p>
    </div>
    <a class="btn btn-primary" href="/gift-cards/">Gift Cards</a>
  </div>
</section>
<section class="wrap visit">
  <p class="eyebrow">Visit us</p>
  <h2>751 Dutchess Turnpike, Poughkeepsie</h2>
  <p class="lead">Open seven days a week &mdash; yes, Sundays too &mdash; 9 AM &ndash; 8 PM &middot; <a href="tel:{{tel}}">{{phone}}</a> &middot; <a class="btn-link" href="/contact/">Directions &amp; contact &rarr;</a></p>
  <p class="serving">Serving Poughkeepsie and the Hudson Valley &mdash; Hyde Park, Wappingers Falls, LaGrange, Pleasant Valley, Fishkill, Hopewell Junction, Rhinebeck, Beacon, New Paltz and Highland.</p>
</section>
""",
 faq=[("Are you open on Sundays?","Yes — Omorfia is open seven days a week, including Sundays and evenings, so a massage, facial or blowout fits around your week instead of the other way around."),
      ("Where is Omorfia Salon & Day Spa located?","We're at 751 Dutchess Turnpike (Route 44), Poughkeepsie, NY 12603 — the former Marlene Weber building, the grey and white building sharing a parking lot with Adams Fairacre Farms, minutes from Arlington and Vassar College."),
      ("Do I need an appointment?","Booking online is the best way to guarantee your time and provider, but call the front desk at (845) 694-4952 and we'll fit you in whenever we can."),
      ("Can I book multiple services in one visit?","Yes — that's the point of a day spa. Stack hair, nails, massage and a facial into one appointment, or let us design the day for you with a package."),
      ("Is Omorfia the former Marlene Weber Day Spa?","Yes — Omorfia opened in July 2024 in the former Marlene Weber Day Spa building at 751 Dutchess Turnpike, under new, local ownership. Same landmark location, a new team and a full salon and spa menu."),
      ("Do you offer couples massage?","Yes — book two massages for the same time and you'll be side by side, or choose the For Two spa package, which pairs massages, facials and pedicures for two guests.")]))

# ---------------------------------------------------------------- services
PAGES.append(service_page("hair","Hair","Hair Salon",
 "Hair Salon in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "Haircuts, color, balayage, extensions and treatments with full pricing at Omorfia, a full-service hair salon in Poughkeepsie, NY.",
 "A hair salon that listens.",
 "Cuts that fall into place, color that reads expensive, and stylists who ask questions before they pick up the shears. Full menu and pricing below.",
 [("Cuts & Styling",[
   ("Haircut Consultation","Complimentary","Talk through the change before the shears come out."),
   ("Women&rsquo;s Cut","$70+","Precision cut for your length and texture, finished with a styled blowout.","$45/month club &mdash; a cut every other month"),
   ("Men&rsquo;s Cut","$55+","Clean, tailored cut &mdash; clippers, shears, or both.","$30/month club &mdash; a cut every month"),
   ("Kids Cut (12 &amp; Under)","$40+","Gentle, patient cuts for our youngest guests."),
   ("Bang Trim","$30+","A quick tune-up between full cuts."),
   ("Wash &amp; Blow Dry","$60+","Shampoo, condition, and a polished blowout.","$30 per blowout &middot; $120/mo for 4"),
   ("Blow Dry Add-On","$25+","Add a finished blowout to any service."),
   ("Hot Tool Finish","$30+","Curls or waves set with a hot tool."),
   ("Flat Iron / Curls","$30+","Sleek and straight, or soft and curled."),
   ("Braiding","$60+","From one statement braid to a fully braided style."),
   ("Half Up / Half Down","$70+","Polished event styling with movement left in."),
   ("Updo","$115+","Full formal styling for weddings, proms, and galas.")]),
  ("Color",[
   ("Color Retouch (Roots)","$100+","Refresh regrowth to match your existing color.","$80/month club &mdash; a root retouch every month"),
   ("All Over Color","$130+","Single-process color from roots to ends."),
   ("Semi-Permanent Color","$95+","Gentle shine and tone that fades gracefully."),
   ("Toner / Glaze","$45+","Neutralize brass and add gloss between services."),
   ("Root Smudge","$35+","Soften the line between roots and color."),
   ("Vivid Hair Consultation","Complimentary","Plan the path to fashion shades before you commit."),
   ("Vivid Color","$200+","Bold fashion shades, applied for staying power."),
   ("Extra Bowl of Color","$35+","For longer, denser hair that needs more product."),
   ("Per Foil","$12+","Add individual foils to any color service.")]),
  ("Highlights & Balayage",[
   ("Face Framing Highlight","$80+","Brightness right where it catches the light."),
   ("Partial Highlight","$180+","Foiled dimension through the top and crown."),
   ("Full Highlight","$220+","All-over foiled dimension, root to ends."),
   ("Baby Lights","$200+","Ultra-fine foils for a sun-kissed, natural finish."),
   ("Balayage Consultation","Complimentary","Map placement and tone before your appointment."),
   ("Partial Balayage","$200+","Hand-painted dimension through the top layers."),
   ("Full Balayage","$320+","Full hand-painted, lived-in color.")]),
  ("Texture & Smoothing",[
   ("Perm","$125+","Lasting curl and body, tailored to your length."),
   ("Keratin Consultation","Complimentary","Find the right smoothing treatment for your hair."),
   ("Keratin Smoothing Treatment (30-Day)","$150+","A frizz-taming reset that lasts about a month."),
   ("Keratin Relaxing Treatment (4-Month)","$350+","Deep smoothing that holds for a season."),
   ("Magic Sleek Treatment","$300+","Salon-grade straightening system for lasting sleekness."),
   ("B Blowout","$250+","Professional smoothing blowout for long-wear frizz control.")]),
  ("Treatments",[
   ("Scalp Treatment","$35+","Exfoliate and rebalance where healthy hair starts."),
   ("Conditioning Treatment","$40+","Deep moisture for dry, thirsty hair."),
   ("Deep Conditioning Mask","$50+","An intensive mask for serious repair."),
   ("Olaplex Hair Treatment","$50+","Bond-rebuilding repair for color-treated hair."),
   ("Aveda Hot Oil Treatment","$50+","Warm botanical oils for shine and softness."),
   ("Kerasilk Recovery Mask","$50+","Luxury smoothing mask for stressed strands."),
   ("Amika Soul Food Mask","$30+","Nourishing moisture mask with a cult following."),
   ("Amika Anti-Frizz Treatment","$20+","A quick humidity shield for smoother wear."),
   ("Rich Repair Serum","$25+","Concentrated repair for damaged lengths."),
   ("Blondes &amp; Highlights Serum","$25+","Tone-protecting care made for lightened hair."),
   ("Color Protecting Serum","$25+","Seal and extend the life of your color."),
   ("60 SEC Bond Pro Mask","$25+","One-minute bond repair added to any visit."),
   ("Malibu C Headlab","$25+","Wellness treatment that lifts mineral buildup."),
   ("L&rsquo;Oreal Prolonger","$15+","An in-salon boost that extends your style&rsquo;s wear."),
   ("Charity Tinsel","$10+","Sparkle strands &mdash; proceeds go to charity.")]),
  ("Extensions",[
   ("Extension Consultation","Complimentary","Match method, length, and color to your goals."),
   ("K-Tip Extensions","$175+","Keratin-bonded strands for seamless length."),
   ("I-Tip Extensions","$150+","Bead-set strands &mdash; no heat, no glue."),
   ("Tape-In Extensions","$125+","Fast, flat, comfortable panels of length."),
   ("Weft Extensions","$300+","A full sewn-in row for maximum fullness."),
   ("Extension Blowdry","$70+","A blowout styled around your extensions."),
   ("Extension Removal","$100+","Safe removal that protects your natural hair.")]),
  ("Head Spa",[
   ("Japanese Head Spa Conditioning Treatment (60 Min)","$150+","A meditative scalp ritual &mdash; cleanse, massage, and condition."),
   ("Japanese Head Spa Facial Treatment (60 Min)","$150+","The head spa ritual, paired with facial care."),
   ("Express Japanese Head Spa","$75+","The signature ritual, condensed.")])],
 [("How do I choose a stylist?","Tell us what you're looking for when you book — the front desk matches new guests with the stylist whose strengths fit the service. Or browse the stylists above and book by name."),
  ("Why are some prices 'starting points'?","Length, density and color history change how much product and time a service takes; your stylist confirms the exact quote before starting."),
  ("Do you do consultations?","Yes — haircut, balayage, vivid, keratin and extension consultations are all complimentary."),
  ("Where is the hair salon?","751 Dutchess Turnpike (Route 44) in Poughkeepsie — the grey and white building that shares a parking lot with Adams Fairacre Farms, about five minutes from Vassar College and Arlington and ten from Marist. Free parking in the lot."),
  ("Do you take walk-ins for haircuts?","When a chair is open, gladly — but booking online or calling (845) 694-4952 is the only way to guarantee a time. We're open seven days, 9 AM to 8 PM, including Sundays."),
  ("Can I get hair and a massage or nails in one visit?","Yes — that's the point of a salon and day spa under one roof. Book them back to back, or pick a spa package and save.")],IMG["hair"],
 kw="Hair Salon in Poughkeepsie, NY &mdash; Cuts, Color, Balayage &amp; Extensions",
 reviews=HAIR_REVIEWS,
 team=("Our stylists","Book a stylist by name",
       [("Georgia Kyriacou","Lead Stylist"),("Hugo Lutin","Master Stylist &amp; Colorist"),("Christie Russell","Senior Stylist &amp; Colorist"),
        ("Patsy Estrada","Stylist, Lash Tech &amp; Makeup"),("Hailey Reed","Senior Stylist &amp; Colorist"),("Katie Obrein","Senior Stylist &amp; Colorist"),
        ("Erin Ohlandt","Stylist &amp; Extension Specialist"),("Juliana Angeles","Stylist"),("Lindy Wilkinson","Master Stylist &amp; Colorist")])))

PAGES.append(service_page("nails","Nails","Nail Salon",
 "Nail Salon in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "Manicures, pedicures, gel, acrylic and dip with full pricing at Omorfia, the nail studio inside Poughkeepsie's full-service day spa.",
 "Clean, calm, meticulous nails.",
 "Spa standards in a nail studio: hospital-grade sanitation, unhurried appointments, and a full menu below.",
 [("Manicures & Pedicures",[
   ("Nail Groom","$20","Shape, buff, and cuticle care &mdash; no polish."),
   ("Regular Manicure","$30","Classic shape, cuticle work, and polish.","$25"),
   ("Regular Pedicure","$45","Soak, shape, callus care, and polish.","$25"),
   ("Spa Manicure","$45","The classic, elevated with exfoliation and massage."),
   ("Spa Pedicure","$65","Extended soak, scrub, mask, and massage."),
   ("Luxury Manicure","$50","Our most indulgent hand ritual."),
   ("Luxury Pedicure","$70","The full throne experience, top to toe.")]),
  ("Gel",[
   ("Gel Manicure","$45","Chip-resistant color cured to a two-week shine."),
   ("Gel Pedicure","$50","Long-wear gel color for sandal-proof toes."),
   ("Luxury Gel Manicure","$60","Gel wear with the full spa treatment."),
   ("Luxury Gel Pedicure","$80","Our richest pedicure, finished in gel."),
   ("New Set Gel X","$75","Full-coverage soft-gel extensions &mdash; light and natural."),
   ("New UV Gel Set","$85","Sculpted UV gel extensions built to last."),
   ("Fill UV Gel Set","$65","Maintenance fill for your UV gel set."),
   ("Gel Soak-Off","$20","Gentle removal that protects the natural nail.")]),
  ("Acrylic & Dip",[
   ("New Set Acrylic","$75","Classic sculpted length and strength."),
   ("Acrylic Fill-In","$70","Keep your set fresh as it grows out."),
   ("Dip Powder","$55","Lightweight, durable color without UV curing.")]),
  ("Finishing Touches",[
   ("French Add-On","$7","The classic white tip on any service."),
   ("Gel French Add-On","$10","A crisp French finish in long-wear gel.")])],
 [("How do you sanitize tools?","Implements are sterilized between every guest and single-use items are exactly that — single use."),
  ("How long does gel last?","Two to three weeks for most guests, depending on your nails and how you use your hands."),
  ("Can I pair nails with another service?","Absolutely — nails and a massage or facial is the most common pairing on our books.")],IMG["nails"],
 kw="Nail Salon in Poughkeepsie, NY &mdash; Manicures, Pedicures, Gel &amp; Dip"))

PAGES.append(service_page("massage","Massage","Massage Therapy",
 "Massage in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "60, 90 and 120 minute massage at Omorfia Day Spa in Poughkeepsie, NY — pay for time, choose Swedish, deep tissue or hot stone when you arrive. Pre-natal and Reiki available.",
 "Massage that melts the week off.",
 "Licensed massage therapists, quiet rooms, and sessions that never feel rushed. <strong>You pay for time, not type</strong> &mdash; book 60, 90 or 120 minutes, then choose Swedish, deep tissue, hot stone or a blend with your therapist when you arrive.",
 [("Massage &middot; Choose your style when you arrive",[
   ("60 Minute Massage","$135","The classic hour &mdash; any style, chosen when you arrive.","$100","The classic hour. You book the time and choose the style with your therapist when you arrive &mdash; Swedish for a full-body reset, deep tissue for stubborn knots, or a blend of both. No decisions required in advance; just come in."),
   ("90 Minute Massage","$195","Full body plus real time on problem areas &mdash; any style, chosen when you arrive.","$160","Ninety minutes gives your therapist real time on problem areas without shortchanging the rest of you. Swedish, deep tissue, or a blend &mdash; decided together when you arrive. You pay for the time, not the type."),
   ("120 Minute Massage","$270","Two unhurried hours, head to toe &mdash; any style, chosen when you arrive.","$235","Two unhurried hours, head to toe. Any style, any combination, chosen with your therapist when you arrive &mdash; the full reset for anyone who never gets enough. You pay for the time, not the type."),
   ("Pre-Natal Massage","$140","Safe, supported comfort for moms-to-be.")]),
  ("Enhancements",[
   ("Hot Stones","$30","Add heated stones to any massage."),
   ("Amethyst Crystals","$30","Crystal-enhanced session for deeper calm."),
   ("Reiki Energy Work","$30","Add energy balancing to your massage."),
   ("Aromatherapy","$10","Essential oils chosen for your session.")]),
  ("Reiki",[
   ("Reiki Service","$125","A full energy-balancing session with a practitioner.")])],
 [("How should I prepare for a massage?","Arrive a few minutes early, hydrate, and tell your therapist about problem areas and pressure preference — then let them work."),
  ("Do I need to choose Swedish or deep tissue when I book?","No — you book the time, not the type. Choose Swedish, deep tissue, hot stone or a blend with your therapist when you arrive, and change your mind on the table if you like. Same price for any style."),
  ("Which length should I book?","60 minutes handles full-body maintenance; 90 gives real focus time on problem areas; 120 is the full reset. Whatever you pick, the style is chosen when you're here."),
  ("Can I get a massage on a Sunday?","Yes — we're open seven days a week, Sundays included, and Sunday massages are a guest favorite. Book online to lock in your time."),
  ("Do you offer gift cards?","Yes — massage is our most-gifted service. Grab one on our gift cards page or at the front desk."),
  ("Do you offer couples massage?","Yes — book two massages for the same time and you'll be treated side by side. For the full afternoon together, the For Two spa package adds facials and pedicures for both of you."),
  ("Are your massage therapists licensed?","Yes — every massage at Omorfia is given by a New York State licensed massage therapist. You can read about Debbie and Nadya on our team page and book either by name."),
  ("Where is Omorfia for massage?","751 Dutchess Turnpike (Route 44) in Poughkeepsie — the grey and white building that shares a parking lot with Adams Fairacre Farms, about five minutes from Vassar College and Arlington and ten from Marist. Free parking, private massage rooms."),
  ("Can I book a same-day massage?","Often, yes — we're open 9 AM to 8 PM seven days a week, so evening and Sunday slots are easier to find here than most places. Book online to see live availability.")],IMG["massage"],
 kw="Massage in Poughkeepsie, NY &mdash; Swedish, Deep Tissue, Hot Stone &amp; Prenatal",
 reviews=MASSAGE_REVIEWS,
 team=("Our therapists","Book a licensed massage therapist by name",
       [("Debbie Cameron","Master Massage Therapist, LMT"),("Nadya Deddrick","Massage Therapist, LMT")])))

PAGES.append(service_page("facials","Facials","Facials & Esthetics",
 "Facials & Waxing in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "Customized facials, advanced treatments and waxing with full pricing at Omorfia Day Spa in Poughkeepsie, NY.",
 "Skin care with a plan.",
 "Every facial starts with a skin analysis and ends with a plan you can follow at home. Facials, advanced treatments and waxing — full menu below.",
 [("Facials",[
   ("Skincare Consultation","Complimentary","Analyze your skin and map the plan."),
   ("European Facial","$135","A luxurious tailored treatment that deeply cleanses, re-balances, and hydrates your skin.","$100","Treat yourself to the ultimate all-in-one skincare indulgence. A timeless skincare essential, this customized treatment is tailored to address your skin&rsquo;s unique needs &mdash; meticulously designed to purify, balance, and hydrate. It begins with a deep cleanse using the T-Zone Balance Cleansing Complex, effectively removing impurities while maintaining skin&rsquo;s natural moisture. A gentle exfoliation follows with the aromatic Honey and Almond Scrub, a natural blend of pure honey, oatmeal, and almond meal, to refine skin texture and promote a smooth, glowing complexion. Unwind with a signature European facial massage performed with Aqua Massage Cream, enhancing circulation and relaxation and preparing your skin for optimal absorption of nutrients. The Balancing Hydrating Mask, enriched with St. John&rsquo;s Wort, Green Tea, and White Tea, soothes and revitalizes, restoring equilibrium to your skin. A customized moisturizer finishes the treatment, leaving skin toned, hydrated, and glowing."),
   ("Anti-Aging Cellusea Massage / Facial","$160","Marine-based firming facial with sculpting massage."),
   ("Redout Facial","$185","A soothing treatment that reduces redness, strengthens the skin barrier, and restores balance.",None,"Discover the ultimate in skin-soothing luxury with this plastic surgeon-approved, clinically tested facial. The treatment harnesses nature&rsquo;s finest ingredients, including Laminaria digitata seaweed, ultra-hydrating hyaluronic acid, and powerful antioxidants like quercetin and rutin, alongside the soothing Mirabilis Jalapa extract. The Red-Out&reg; Facial begins with a gentle cleanse, followed by Red-Out&reg; Soothing Essence Mist to prep and awaken the skin. Next, the powerful Red-Out&reg; Serum is applied and massaged in, hydrating and temporarily reducing the appearance of redness and dryness. An intensive calming mask visibly soothes, while Eye Rescue Pads provide an indulgent eye contour treatment designed to reduce puffiness. Another splash of Soothing Essence Mist and a final application of Red-Out&reg; Soothing Moisturizer complete this rejuvenating treatment, leaving skin refreshed and radiant. Experience the ultimate sanctuary for sensitive skin."),
   ("Biolight Facial","$200","Gently resurfaces, refines and revitalizes &mdash; diminishing the look of dark spots and discoloration.",None,"Experience the miracle of flawless, luminous skin through the Rep&ecirc;chage&reg; Biolight&reg; Miracle Facial, a breakthrough treatment that helps fade the look of dark spots, evens skin tone, and restores brilliance without compromising delicate skin. Powered by Laminaria digitata seaweed, this facial enriches skin with essential nutrients, while the Glyco-Sea&reg; Glycolic Peel gently resurfaces, smoothing away dullness and imperfections. Brightening agents like Licorice Root Extract and clinically proven Daisy Flower Extract help reduce the look of hyperpigmentation, restoring clarity and an even-toned glow. Gotu Kola (CICA) and Willow Bark Extract soothe and refine, leaving skin perfectly hydrated and balanced. Each step is carefully designed to resurface, hydrate, and illuminate, making way for a complexion that looks flawlessly smooth, youthful, and radiant."),
   ("Back Facial","$200","The full facial protocol for hard-to-reach skin."),
   ("Extraction Facial","$235","Thorough, methodical decongestion of the pores."),
   ("Vita Cura Facial","$250","The ultimate age-defying facial &mdash; enzymatic micropeel, two massages, firming seaweed mask and an instant lift.",None,"Endorsed by plastic surgeons for its remarkable firming and rejuvenating effects, the Vita Cura&reg; 5 Phase Firming Facial is designed to restore youthful vitality to mature skin. This luxurious treatment begins with an Enzymatic Micropeel, infused with Papaya Enzyme and Salicylic Acid, to gently exfoliate and reveal a more even-toned, radiant complexion. Two targeted massages follow, using the Vita Cura&reg; Renewal Serum and Triple Firming Cream, enriched with Laminaria digitata Seaweed Extract, Hyaluronic Acid, Ginkgo Biloba, and Horse Chestnut Extracts, to deeply hydrate and refine skin texture. A cooling Spirulina Seaweed Mask, formulated with bio-mimetic pentapeptide, firms and smooths the skin, visibly reducing fine lines and wrinkles. The final step, Vita Cura&reg; Opti-Lift&reg; Serum, harnesses the power of Acetyl Hexapeptide-8 and Pure Almond Protein Biopolymer, delivering an immediate lifting effect for a sculpted, youthful glow &mdash; the perfect non-invasive alternative for those seeking plastic surgeon-recommended results without downtime. Always wear sun protection for one week after the treatment and avoid sun exposure."),
   ("Triple Action Cryogenic Facial","$285","Advanced peptides, cooling cryo-therapy and nutrient-rich seaweed to visibly lift and smooth.",None,"Experience next-generation age management with the Triple Action Lift Peptide Cryo Facial, a transformative treatment designed to visibly firm, hydrate, and rejuvenate the skin. This facial begins with a layered application of peptide-enriched serums, followed by two invigorating facial massages that stimulate circulation and enhance absorption. A dual-layer mask system &mdash; combining cryo-cooling technology with marine minerals &mdash; revives the skin&rsquo;s appearance, helping to improve visible tone and support a firmer, more contoured look. Laminaria digitata seaweed and advanced peptides work in synergy to refine skin texture, smooth the look of fine lines, and restore a lifted, radiant glow. Ideal for all skin types seeking a non-invasive yet high-performance treatment, this facial delivers long-lasting hydration and visible rejuvenation."),
   ("Extraction Hydrogen-Oxygen Facial","$325","Deep extraction plus hydrating oxygen infusion.")]),
  ("Advanced & Add-On Treatments",[
   ("Microdermabrasion","$35","Mechanical exfoliation for texture and tone."),
   ("Glycolic Acid Treatment","$50","Chemical exfoliation for glow and smoothness."),
   ("Peptide Mask","$50","Firming peptides in a single treatment mask."),
   ("Rep&ecirc;chage Eye Treatment","$50","Fades dark circles, smooths fine lines and banishes puffiness for a lifted, youthful gaze.",None,"Turn back the clock on tired eyes with the transformative Opti-Firm&reg; Eye Contour Treatment. This professional therapy targets the delicate eye area to diminish dark circles, puffiness, and wrinkles. Harnessing the power of peptides, seaweed extracts, and clinically proven ingredients, it works to firm and smooth the eye contour, restoring a rested and vibrant appearance. Let your eyes reflect newfound vitality as they appear more lifted, luminous, and refreshed."),
   ("Exfoliating Lip Treatment","$10","Smooth, conditioned lips in minutes."),
   ("Red Light Therapy","$20","LED light to support collagen and calm."),
   ("High Frequency Acne Treatment","$20","Targeted current to help clear breakouts.")]),
  ("Waxing",[
   ("Brow Wax","$30","Shape and define the arch.","$22/month club &mdash; a brow wax every month"),
   ("Lip Wax","$21","Quick, clean upper-lip removal."),
   ("Full Face Wax","$60","Brow, lip, chin, and cheeks in one visit."),
   ("Neck Wax","$23","Clean up the neckline."),
   ("Underarm Wax","$37","Smooth results that outlast shaving."),
   ("Half Arm Wax","$47","Elbow down, silky smooth."),
   ("Full Arm Wax","$58","Shoulder to wrist."),
   ("Chest Wax","$74","Full chest, done properly."),
   ("Back Wax","$74","Full back, shoulder to waist."),
   ("Half Leg Wax","$58","Knee down &mdash; the sandal essential."),
   ("Full Leg Wax","$84","Hip to ankle, completely smooth."),
   ("Bikini Wax","$50","Clean lines along the bikini edge."),
   ("French Bikini Wax","$70","Higher and deeper than the classic bikini."),
   ("Brazilian Wax","$80","Everything, or nearly everything &mdash; your call.")])],
 [("How often should I get a facial?","Every four to six weeks matches your skin's natural cycle; your esthetician will recommend a cadence for your goals."),
  ("Will my skin be red afterward?","A signature facial leaves most guests glowing, not red. Stronger treatments can bring brief redness — we'll tell you exactly what to expect before we start."),
  ("What about medical aesthetics?","For injectables and medical-grade treatments, our sister practice OMO Med Spa has you covered — ask the front desk.")],IMG["facials"],
 note="We are a proud Rep&ecirc;chage&reg; spa partner using their professional skincare products and treatments for these services. The trademarks used in this menu and all rights thereto belong exclusively to Sarkli-Rep&ecirc;chage, Ltd. All rights reserved.",
 kw="Facials &amp; Waxing in Poughkeepsie, NY"))

PAGES.append(service_page("lashes-brows","Lashes & Brows","Lash Extensions and Brows",
 "Lash Extensions & Brows in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "Classic and hybrid lash extensions, lash lifts, tints, brow lamination and microblading with full pricing at Omorfia in Poughkeepsie, NY.",
 "Wake up ready.",
 "Lash extensions, lifts and tints that make mascara optional &mdash; and brow work that frames the whole face. Full menu and pricing below.",
 [("Lash Extensions",[
   ("Classic Full Set","$150","One extension per lash for everyday definition."),
   ("Classic 2 Week Fill","$65","Top up your classic set at two weeks."),
   ("Classic 3 Week Fill","$75","A fuller refresh at the three-week mark."),
   ("Hybrid Full Set","$190","Classic strands mixed with volume fans."),
   ("Hybrid 2 Week Fill","$75","Keep your hybrid set dense at two weeks."),
   ("Hybrid 3 Week Fill","$85","The three-week hybrid refresh."),
   ("Individual Lashes","$60","Clusters placed exactly where you want impact.")]),
  ("Lifts & Tints",[
   ("Lash Lift &amp; Tint","$95","Curl and darken your natural lashes for weeks."),
   ("Lash Tint","$25","Mascara-dark lashes, zero daily effort."),
   ("Brow Tint","$25","Richer, fuller-looking brows in minutes."),
   ("Brow Lamination &amp; Tint","$100","Brushed-up, set-in-place brows with tint.")]),
  ("Brows",[
   ("Brow Wax","$30","Shape and define the arch.","$22/month club &mdash; a brow wax every month"),
   ("Microblading","$450","Hair-stroke brow tattooing for natural fullness."),
   ("Microblade Fill","$250","Refresh strokes and color on existing work.")])],
 [("How often do lash extensions need fills?","Every two to three weeks keeps a set full — that's why fills are priced at both marks."),
  ("Classic or hybrid?","Classic is one extension per natural lash for an everyday look; hybrid mixes in volume fans for noticeably fuller, still-natural lashes."),
  ("How long does microblading last?","Twelve to eighteen months for most guests, with a fill recommended to keep the strokes crisp.")],IMG["makeup"],
 kw="Lash Extensions, Lash Lifts &amp; Brows in Poughkeepsie, NY"))

PAGES.append(service_page("tanning","Tanning","Tanning",
 "Spray Tanning in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "Show Stopper sunless glow — upper body $40, full body $80 — at Omorfia Day Spa in Poughkeepsie, NY.",
 "A glow without the guesswork.",
 "Even, natural-looking color with none of the orange and none of the streaks &mdash; timed to peak exactly on your event day.",
 [("Sunless Glow",[
   ("Show Stopper Upper Body Glow","$40","Face, arms, and shoulders &mdash; camera-ready."),
   ("Show Stopper Full Body Glow","$80","Head-to-toe color, matched to your skin tone.")])],
 [("When should I tan before an event?","One to two days before is the sweet spot — the color settles and any guide bronzer washes away."),
  ("How do I make it last?","Exfoliate before your session, then moisturize daily and keep long hot showers to a minimum."),
  ("Will it look natural?","That's the entire job. We match depth of color to your skin tone so it reads sun, not spray.")],IMG["tanning"],
 kw="Spray Tanning in Poughkeepsie, NY"))

PAGES.append(service_page("makeup","Makeup","Makeup Artistry",
 "Makeup Artist in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 "Professional makeup application, lashes and bridal artistry with pricing at Omorfia Day Spa in Poughkeepsie, NY.",
 "Makeup for the days that matter.",
 "Camera-ready artistry for events and photoshoots. For weddings and bridal parties, see our full Wedding &amp; Bridal menu.",
 [("Makeup Artistry",[
   ("Traditional Application","$100","Full-face artistry for events and nights out."),
   ("Strip Lashes","$15","Applied with any makeup service."),
   ("Lash Clusters","$40","Buildable clusters for tailored drama.")]),
  ("Bridal",[
   ("Bridal Trial Makeup","$85","Lock the look before the big day."),
   ("Full Bridal Menu","See Wedding &amp; Bridal","Hair, makeup, and the whole party &mdash; on one timeline.")])],
 [("Should I book a trial?","For weddings, always. It locks the look, the timing and the products before the day itself."),
  ("Do you work with lashes?","Yes — strip lashes and clusters for events, and full lash extensions through our esthetics studio."),
  ("Can my whole party get ready here?","Yes — hair, makeup and nails for the full party is exactly what a day spa is for. See Wedding & Bridal.")],IMG["makeup"],
 kw="Makeup Artist in Poughkeepsie, NY"))

# ---------------------------------------------------------------- wedding
PAGES.append(dict(path="wedding",nav="Wedding & Bridal",service="Bridal Hair and Makeup",
 title="Bridal Hair & Makeup in Poughkeepsie, NY | Hudson Valley Weddings | Omorfia",
 desc="Wedding hair, bridal makeup, nails and bridal-party services in Poughkeepsie, NY. Trials, timelines and full bridal-party mornings for Hudson Valley weddings at Omorfia Salon & Day Spa.",
 body=f"""
<section class="page-hero has-photo" style="background-image:url('{IMG["wedding"]}')">
  <div class="ph-inner">
    <h1 class="eyebrow">Bridal Hair &amp; Makeup in the Hudson Valley</h1>
    <p class="ph-title">The morning your day begins.</p>
    <p class="lead">Hair, makeup and nails for brides and bridal parties &mdash; run on a real timeline, by a team that does this every weekend. One roof, zero chaos, champagne optional.</p>
    <a class="btn btn-primary" href="{{book}}">Start Your Bridal Booking</a>
  </div>
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">For the bride</p>
    <h2>Trial first, always</h2>
    <p>Every bridal booking starts with a trial: we lock the look, the products, and the exact timing before the day itself. On the morning, your only job is to sit still and be celebrated.</p>
  </div>
  <div>
    <p class="eyebrow">For the party</p>
    <h2>The whole crew, one roof</h2>
    <p>Bridesmaids, moms, flower girls &mdash; we schedule the full party across our hair, makeup and nail teams so everyone finishes on time and no one is fighting over a hotel mirror.</p>
  </div>
</section>
<section class="wrap">
  <p class="eyebrow">How it works</p>
  <h2>Three steps to the aisle</h2>
  {svc_list([("1. Consult","Tell us the date, the venue, the party size and the vibe — we'll map the morning."),
             ("2. Trial","Bride's hair and makeup trial, photographed in daylight, refined until it's exactly right."),
             ("3. The day","A locked timeline, your full party styled in sequence, everyone out the door on schedule.")])}
  <p class="menu-note">Weekend dates book far in advance &mdash; reach out as soon as you have a date. Call <a href="tel:{{tel}}">{{phone}}</a> or book a consultation online.</p>
</section>
<section class="wrap menu-wrap">
  <p class="eyebrow">Bridal menu</p>
  <h2>Wedding day pricing</h2>
  """+menu_html([("The Bride",[
  ("Bridal Trial Hair &amp; Makeup","$300","The full run-through, refined until it&rsquo;s exactly right."),
  ("Bridal Hair","$400","The morning-of style, executed on a timeline."),
  ("Bridal Makeup","$150","Camera-proof artistry that lasts past the last dance."),
  ("Bridal Lashes","$25","The finishing flutter.")]),
 ("The Party",[
  ("Bridal Party Member Hair","$150","Event styling for each member of the party."),
  ("Bridal Party Makeup","$115","Coordinated looks for the whole crew."),
  ("Groom Haircut","$55","Sharp and wedding-ready.")]),
 ("Pre-Wedding Glow",[
  ("Bridal Express Facial","$80","A pre-wedding glow, timed to the week of."),
  ("Bridal Facial Wax","$65","Clean, photo-ready definition."),
  ("Bridal 60-Min Massage","$150","An hour of calm before the chaos."),
  ("Bridal 90-Min Massage","$200","Ninety minutes, for nerves that need it.")])], "wedding")+"""
  <p class="menu-note">Party pricing is per person. Your consultation locks the full quote and the morning-of timeline.</p>
</section>
""",
 faq=[("How far in advance should we book?","As soon as you have a date — popular Hudson Valley wedding weekends fill months out, and your trial should happen four to eight weeks before the day."),
      ("Can you handle large bridal parties?","Yes — with hair, makeup and nail teams under one roof we sequence large parties without the bottleneck of a single traveling artist."),
      ("Do you offer on-site services?","Ask during your consultation — depending on the date, venue and party size we'll recommend in-salon or discuss on-location options."),
      ("What about grooms and guests?","Cuts, styling, and a pre-wedding glow-up for anyone in the party — everyone's welcome on the timeline.")],faq_done=False))

# ---------------------------------------------------------------- specials
PAGES.append(dict(path="specials",nav="Specials",service="New Guest Offers",
 title="Specials & New Guest Offer | Omorfia Salon & Day Spa, Poughkeepsie NY",
 desc="New to Omorfia? See our new-guest introductory offer and seasonal specials at Poughkeepsie's full-service salon and day spa.",
 body="""
<section class="page-hero">
  <p class="eyebrow">Specials &middot; New guests</p>
  <h1>First time? We&rsquo;d love to meet you.</h1>
  <p class="lead">New guests get <strong>$15 off their first visit</strong> &mdash; mention it when you book, or ask the front desk. Seasonal specials rotate throughout the year and land on this page and our Instagram first.</p>
  <a class="btn btn-primary" href="{book}">Book Your First Visit</a>
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">Introductory offer</p>
    <h2>Your first visit, welcomed</h2>
    <p><strong>$15 off your first visit.</strong> It&rsquo;s our way of making the first appointment an easy yes. One per guest, on your first visit &mdash; mention it when you book.</p>
  </div>
  <div>
    <p class="eyebrow">Seasonal</p>
    <h2>Current specials</h2>
    <p>Back-to-school, holiday and seasonal specials are posted here and on <a href="https://www.instagram.com/omorfiadayspa/" rel="noopener">Instagram</a> as they run. Follow along or ask the front desk what&rsquo;s on this month.</p>
  </div>
</section>
""",
 kw="New Guest Offer &amp; Specials &mdash; Poughkeepsie Salon &amp; Day Spa",
 faq=[("Who counts as a new guest?","Anyone visiting Omorfia for the first time — welcome!"),
      ("Can I combine specials?","One offer per visit; the front desk will always apply whichever saves you the most."),
      ("How do I hear about specials first?","Follow us on Instagram — seasonal offers post there the day they launch.")]))

# ---------------------------------------------------------------- gift cards
PAGES.append(dict(path="gift-cards",nav="Gift Cards",service="Gift Cards",
 title="Gift Cards | Omorfia Salon & Day Spa, Poughkeepsie NY",
 desc="Give the gift of a spa day in Poughkeepsie, NY. Omorfia gift cards work across every service — hair, massage, facials, nails and packages.",
 body="""
<section class="page-hero">
  <p class="eyebrow">Gift cards</p>
  <h1>The gift nobody returns.</h1>
  <p class="lead">An Omorfia gift card works across everything we do &mdash; a massage, a color appointment, a full spa-day package, or simply a card loaded with an amount and left to their imagination.</p>
  <a class="btn btn-primary" href="{gift}">Buy a Gift Card</a>
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">Online</p>
    <h2>Buy in a minute</h2>
    <p>Purchase online and it&rsquo;s delivered by email &mdash; perfect for the birthday you remembered at 11 PM. Any amount, redeemable across all services.</p>
  </div>
  <div>
    <p class="eyebrow">In person</p>
    <h2>Or from the front desk</h2>
    <p>Prefer a physical card in an envelope? Stop by 751 Dutchess Turnpike or call <a href="tel:{tel}">{phone}</a> and we&rsquo;ll have it ready for pickup.</p>
  </div>
</section>
""",
 kw="Spa Gift Cards in Poughkeepsie, NY",
 faq=[("Do gift cards expire?","Ask the front desk for current terms — we keep them as generous as New York law allows."),
      ("Can a gift card be used on packages?","Yes — gift cards apply to any service, package or product we offer."),
      ("Can I gift a specific service?","Absolutely — tell us the service (a couples massage is the crowd favorite) and we'll load the card to match.")]))


# ---------------------------------------------------------------- team
TEAM_GROUPS = [
 ("mgmt","Management",[
   ("Georgia Kyriacou","Founder of Omorfia Day Spa &amp; Lead Stylist","georgia.jpg",
    "Georgia founded Omorfia to build the salon she always wanted to work in &mdash; and she still spends her days behind the chair as lead stylist, setting the standard for the whole room."),
   ("Stavros Kyriacou","Owner of Kyriacou Beauty Group","stavros.jpg",
    "Stavros leads Kyriacou Beauty Group, the family behind Omorfia, OMO Med Spa, and Kyriacou Cosmetics. At Omorfia he minds the guest experience &mdash; the details you feel but never see."),
 ]),
 ("sty","Stylists",[
   ("Lindy Wilkinson","Master Stylist, Colorist &amp; Owner of The Mane Event Salon",None,
    "A master stylist and colorist who also owns The Mane Event Salon &mdash; the kind of veteran hands guests request by name."),
   ("Hugo Lutin","Master Stylist &amp; Colorist","hugo.jpg",
    "Master-level cutting and color &mdash; Hugo is the calm, exacting presence guests trust with their biggest changes."),
   ("Christie Russell","Senior Stylist &amp; Colorist","christie.jpg",
    "Christie listens first, then delivers exactly the hair you described &mdash; guests say so by name in our Google reviews."),
   ("Patsy Estrada","Senior Stylist, Colorist, Lash Tech &amp; Makeup Artist","patsy.jpg",
    "Stylist, colorist, lash tech and makeup artist &mdash; Patsy is the one to book when the whole look has to come together."),
   ("Hailey Reed","Senior Stylist &amp; Colorist",None,
    "Senior stylist and colorist with an eye for wearable, modern color."),
   ("Katie Obrein","Senior Stylist &amp; Colorist","katie.jpg",
    "Senior stylist and colorist focused on cuts that grow out as well as they photograph."),
   ("Erin Ohlandt","Junior Stylist, Colorist &amp; Extension Specialist","erin.jpg",
    "Stylist, colorist, and our extension specialist &mdash; length and fullness that pass the touch test."),
   ("Juliana Angeles","Stylist",None,
    "Stylist with fresh technique and an easy chair-side manner &mdash; ask for Juliana for cuts, color and blowouts."),
   ("Nevaeh Pittman","Junior Stylist &amp; Nail Tech",None,
    "Junior stylist and nail tech &mdash; Nevaeh moves between the chair and the nail table, so hair and nails can happen in one visit."),
 ]),
 ("mas","Massage Therapists",[
   ("Debbie Cameron","Master Massage Therapist","debbie.jpg",
    "Master massage therapist &mdash; guests call her hands &ldquo;truly magical&rdquo; in our Google reviews, and they&rsquo;re not wrong."),
   ("Nadya Deddrick","Massage Therapist","nadya.jpg",
    "Massage therapist with a steady, therapeutic touch for tension that&rsquo;s overstayed its welcome."),
 ]),
 ("est","Estheticians",[
   ("Gigi Currie","Master Esthetician &amp; Makeup Artist","gigi.jpg",
    "Master esthetician and makeup artist &mdash; skin analysis, corrective facials, and camera-ready artistry."),
 ]),
 ("nai","Nail Technicians",[
   ("Sandy Bach","Master Nail Tech &amp; Artist","sandy.jpg",
    "Master nail tech and artist &mdash; meticulous shaping, long-wear finishes, and detail work worth photographing."),
 ]),
]

def team_section():
    cards=[]; modals=[]
    idx=0
    for key,label,members in TEAM_GROUPS:
        for name,role,img,bio in members:
            first = name.split()[0]
            if img:
                media=f'<img src="/images/team/{img}" alt="{name}" loading="lazy">'
                mmedia=f'<img src="/images/team/{img}" alt="{name}">'
            else:
                media=f'<span class="tp-ph" aria-hidden="true">{name.strip()[0]}</span>'
                mmedia=f'<span class="tp-ph tm-ph" aria-hidden="true">{name.strip()[0]}</span>'
            cards.append(
              f'<div class="tp-card" role="button" tabindex="0" data-open="tm-{idx}" aria-haspopup="dialog">'
              f'{media}<p class="tm-name">{name}</p><p class="tm-role">{role}</p></div>')
            modals.append(
              f'<div class="tmodal" id="tm-{idx}" role="dialog" aria-modal="true" aria-label="{name}" hidden>'
              f'<div class="tm-back" data-tclose></div>'
              f'<div class="tm-card"><button class="tm-x" data-tclose aria-label="Close">&times;</button>'
              f'<div class="tm-media">{mmedia}</div>'
              f'<div class="tm-info"><p class="eyebrow">{role}</p><h3>{name}</h3>'
              f'<p class="tm-bio">{bio}</p>'
              f'<a class="btn btn-primary" href="{{book}}">Book with {first}</a> '
              f'<a class="btn-link tm-more" href="/team/{slugify(name)}/">Full profile &rarr;</a></div>'
              f'</div></div>')
            idx+=1
    js = """<script>
(function(){
  if(window.__omModal)return; window.__omModal=1;
  function open(id){var m=document.getElementById(id);if(!m)return;m.hidden=false;document.documentElement.classList.add('op-lock');}
  function closeAll(){document.querySelectorAll('.tmodal').forEach(function(m){m.hidden=true;});document.documentElement.classList.remove('op-lock');}
  document.addEventListener('click',function(e){
    var c=e.target.closest('[data-open]');
    if(c){open(c.getAttribute('data-open'));return;}
    if(e.target.closest('[data-tclose]'))closeAll();
  });
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape')closeAll();
    if(e.key==='Enter'||e.key===' '){
      var c=document.activeElement;
      if(c&&c.hasAttribute&&c.hasAttribute('data-open')){e.preventDefault();open(c.getAttribute('data-open'));}
    }
  });
})();
</script>"""
    return ('<div class="tgroup tgroup-all">'+"".join(cards)+'</div>'
            + "".join(modals) + js)

ALL_PERSONS = [(n, r.replace("&amp;","&"), _i) for _,_,ms in TEAM_GROUPS for n,r,_i,_b in ms]

PAGES.append(dict(path="team",nav="Meet the Team",
 title="Meet the Team | Omorfia Salon & Day Spa, Poughkeepsie NY",
 desc="Meet the stylists, massage therapists, estheticians and nail technicians behind Omorfia Salon & Day Spa in Poughkeepsie, NY.",
 persons=ALL_PERSONS,
 body="""
<section class="wrap team-intro">
  <h1 class="eyebrow">Meet the Omorfia Team &middot; Stylists, Therapists &amp; Estheticians in Poughkeepsie</h1>
  <p class="ph-title">The hands behind the calm.</p>
</section>
<section class="wrap team-wrap">
  """+team_section()+"""
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">How we work</p>
    <h2>Craft, kept sharp</h2>
    <p>Our team trains continuously &mdash; cutting, color, skin and technique education throughout the year &mdash; because the standard that built this place only holds if it keeps rising.</p>
  </div>
  <div>
    <p class="eyebrow">Join us</p>
    <h2>Talent, welcome</h2>
    <p>We&rsquo;re always glad to meet exceptional stylists, therapists and nail artists. Introduce yourself at the front desk, reach out through <a href="https://www.instagram.com/omorfiadayspa/" rel="noopener">Instagram</a>, or email <a href="mailto:Stavros@kyriacoubeauty.com">Stavros@kyriacoubeauty.com</a>.</p>
  </div>
</section>
<section class="wrap team-index">
  <p class="eyebrow">Profiles</p>
  <h2>Book by name</h2>
  """+"".join(f'<p class="team-index-group"><strong>{label}:</strong> '+" &middot; ".join(f'<a href="/team/{slugify(n)}/">{n}</a>' for n,_r,_i,_b in members)+'</p>' for _k,label,members in TEAM_GROUPS)+"""
</section>
""",
 faq=None))

# ---------------------------------------------------------------- team bio pages (/team/<name>/)
# One landing page per provider: Person schema + real reviews + services. These are the pages
# practitioner Google Business Profiles (e.g. "Debbie Cameron, LMT") link to.
_BIO_SVC = {
 "sty": ("Hair Stylist", "hair", [("/hair/","Cuts &amp; blowouts"),("/balayage/","Balayage &amp; highlights"),("/hair/","Color"),
                                  ("/keratin-treatment/","Keratin smoothing"),("/hair-extensions/","Hair extensions"),("/wedding/","Bridal &amp; event hair")],
         ["Haircuts","Hair color","Balayage","Highlights","Blowouts","Keratin smoothing","Hair extensions","Updos"], None),
 "mas": ("Licensed Massage Therapist", "massage", [("/massage/","60 / 90 / 120 minute massage"),("/deep-tissue-massage/","Deep tissue"),
                                  ("/massage/","Swedish &amp; hot stone"),("/prenatal-massage/","Prenatal massage"),("/couples-massage/","Couples massage"),("/packages/","Spa packages")],
         ["Swedish massage","Deep tissue massage","Hot stone massage","Prenatal massage","Couples massage","Therapeutic massage"],
         "New York State Licensed Massage Therapist (LMT)"),
 "est": ("Esthetician", "facials", [("/facials/","Facials"),("/brazilian-wax/","Waxing"),("/lashes-brows/","Lashes &amp; brows"),("/makeup/","Makeup")],
         ["Facials","Skin care","Waxing","Lash extensions","Brow shaping","Makeup"], None),
 "nai": ("Nail Technician", "nails", [("/nails/","Manicures &amp; pedicures"),("/nails/","Gel, acrylic &amp; dip"),("/memberships/","Mani &amp; Pedi Club")],
         ["Manicures","Pedicures","Gel nails","Acrylic nails","Dip powder","Nail art"], None),
 "mgmt": ("Salon &amp; Spa", "hero", [("/hair/","Hair"),("/massage/","Massage"),("/facials/","Facials"),("/nails/","Nails")],
         ["Salon management","Hair styling","Guest experience"], None),
}
def bio_page(group, name, role, img, bio):
    first = name.split()[0]
    slug  = slugify(name)
    kind, imgkey, links, knows, cred = _BIO_SVC[group]
    role_plain = html.unescape(role)
    if group=="mgmt" and "Stylist" in role: kind, imgkey, links, knows = "Hair Stylist", "hair", _BIO_SVC["sty"][2], _BIO_SVC["sty"][3]
    if group=="sty" and "Nail" in role: links = links + [("/nails/","Manicures &amp; pedicures")]; knows = knows + ["Manicures","Pedicures"]
    if group=="sty" and "Lash" in role: links = links + [("/lashes-brows/","Lashes &amp; brows"),("/makeup/","Makeup")]; knows = knows + ["Lash extensions","Makeup"]
    kw = f"{name} &mdash; {kind} in Poughkeepsie, NY"
    rvs = person_reviews(first)
    rv = ""
    if rvs:
        rv = (f'<section class="wrap reviews-wrap"><p class="eyebrow">Google reviews</p><h2>What guests say about {first}</h2>'
              f'{review_cards(rvs)}<p class="menu-note"><a class="btn-link" href="/reviews/">More reviews &rarr;</a></p></section>')
    menu_url   = f"/{imgkey}/" if imgkey!="hero" else "/menu/"
    menu_label = {"hair":"Full hair menu &amp; prices","massage":"Massage menu &amp; prices","facials":"Facials &amp; waxing menu","nails":"Nail menu &amp; prices"}.get(imgkey,"Services &amp; prices")
    media = f'<img class="bio-photo" src="/images/team/{img}" alt="{name}, {html.escape(role_plain)} at Omorfia Salon &amp; Day Spa in Poughkeepsie, NY" width="900" height="900">' if img else ""
    svc = " &middot; ".join(f'<a href="{u}">{t}</a>' for u,t in links)
    faq = [(f"How do I book with {first}?", f"Book online and choose {first} as your provider, or call (845) 694-4952 and ask for {first}. We're open seven days, 9 AM to 8 PM."),
           (f"Where does {first} work?", f"At Omorfia Salon & Day Spa, 751 Dutchess Turnpike (Route 44), Poughkeepsie, NY 12603 — the grey and white building sharing a lot with Adams Fairacre Farms, minutes from Arlington, Vassar College and Marist. Free parking."),
           (f"What does {first} specialize in?", f"{html.unescape(re.sub('<[^>]+>','',bio))}")]
    body=f"""
<section class="page-hero has-photo ph-noslides bio-hero" style="background-image:url('{IMG[imgkey]}')">
  <div class="ph-inner">
    <h1 class="eyebrow">{kw}</h1>
    <p class="ph-title">{first}, {role}</p>
    <p class="lead">{bio}</p>
    <a class="btn btn-primary" href="{{book}}">Book with {first}</a>
  </div>
</section>
<section class="wrap split bio-wrap">
  <div class="bio-media">{media}</div>
  <div>
    <p class="eyebrow">{kind} &middot; Omorfia Salon &amp; Day Spa</p>
    <h2>{first} at Omorfia</h2>
    <p>{bio}</p>
    <p><strong>Book {first} for:</strong> {svc}</p>
    <p class="serving">Serving guests from Poughkeepsie, Hyde Park, Wappingers Falls, LaGrange, Fishkill, Rhinebeck, Beacon and across the Hudson Valley.</p>
    <p class="bio-cta"><a class="btn btn-primary" href="{{book}}">Book with {first}</a> <a class="btn-link" href="tel:{PHONE_TEL}">or call {PHONE}</a></p>
  </div>
</section>
{rv}
{faq_html(faq)}
<section class="wrap related"><p class="eyebrow">Explore</p><h2>You might also be looking for</h2><p class="related-links"><a href="/team/">Meet the whole team</a> &middot; <a href="{menu_url}">{menu_label}</a> &middot; <a href="/reviews/">Reviews</a> &middot; <a href="/contact/">Contact &amp; hours</a></p></section>
"""
    if img: OG_IMG[f"team/{slug}"] = f"/images/team/{img}"
    return dict(path=f"team/{slug}", nav=name, parent="team",
        title=f"{name} – {role_plain} in Poughkeepsie, NY | Omorfia Salon & Day Spa",
        desc=f"{name} is a {role_plain.lower()} at Omorfia Salon & Day Spa, 751 Dutchess Turnpike, Poughkeepsie, NY. Read reviews and book with {first} online or call (845) 694-4952.",
        body=body, faq=faq, faq_done=True,
        person=dict(name=name, role=role_plain, desc=html.unescape(re.sub('<[^>]+>','',bio)), img=img, knows=knows, credential=cred))

for _k,_label,_members in TEAM_GROUPS:
    for _n,_r,_i,_b in _members:
        PAGES.append(bio_page(_k,_n,_r,_i,_b))

# ---------------------------------------------------------------- reviews
PAGES.append(dict(path="reviews",nav="Reviews",kw="Omorfia Reviews &mdash; Poughkeepsie Salon &amp; Day Spa",
 title="Reviews | Omorfia Salon & Day Spa, Poughkeepsie NY",
 desc="What guests say about Omorfia Salon & Day Spa in Poughkeepsie, NY — hair, massage, facials, nails and more. Read reviews and leave your own.",
 body=f"""
<section class="page-hero">
  <p class="eyebrow">Reviews</p>
  <h1>Don&rsquo;t take our word for it.</h1>
  <p class="lead"><strong>4.9 stars across 150+ Google reviews.</strong> The Hudson Valley has been generous to us &mdash; here&rsquo;s a little of what guests say, straight from Google. And if we&rsquo;ve earned it, a review is the single nicest thing you can do for a local business.</p>
</section>
<section class="wrap">
  {review_cards(REVIEWS)}
  <p class="center" style="margin-top:34px">
    <a class="btn btn-primary" href="https://search.google.com/local/writereview?placeid=ChIJa3T8WRM_3YkR99abqa-Z1dQ" rel="noopener">Review Us on Google</a>
    <a class="btn btn-outline" href="https://search.google.com/local/reviews?placeid=ChIJa3T8WRM_3YkR99abqa-Z1dQ" rel="noopener">Read All Reviews on Google</a>
  </p>
</section>
""",
 faq=None))

# ---------------------------------------------------------------- packages
PAGES.append(dict(path="packages",nav="Packages",service="Spa Packages",
 title="Spa Packages in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 desc="Curated spa day packages at Omorfia in Poughkeepsie, NY — bundle massage, facials, hair and nails into one visit and save over à la carte.",
 body="""
<section class="page-hero">
  <p class="eyebrow">Packages &middot; Design your day</p>
  <h1>One booking. A whole spa day.</h1>
  <p class="lead">Our packages bundle the services people already stack together &mdash; massage, facial, nails, hair &mdash; into a single appointment at a saving over booking each &agrave; la carte. Arrive once, hand over your afternoon, leave new.</p>
  <a class="btn btn-primary" href="{book}">Book a Package</a>
</section>
<section class="wrap pkg-wrap">
  <div class="pkg-grid">
    <div class="pkg">
      <p class="eyebrow">Classic Spa Day</p>
      <p class="pkg-price">$370<span>a $440 value &middot; save $70</span></p>
      <p class="pkg-time">About 4 hours</p>
      <ul class="pkg-list">
        <li>60 Minute Massage</li>
        <li>European Facial</li>
        <li>Spa Manicure</li>
        <li>Spa Pedicure</li>
        <li>Wash &amp; Blowout</li>
      </ul>
      <p class="pkg-desc">The complete spa day &mdash; massage, facial, hands, feet, and a blowout to finish. Everything people mean when they say &ldquo;spa day.&rdquo;</p>
      <a class="btn btn-primary" href="#book" data-blvd-path="/cart/menu/Packages/p_74231a9e-5a21-43b6-af37-7432227b2256" data-blvd-type="PACKAGE">Buy the Classic Spa Day</a>
    </div>
    <div class="pkg pkg-featured">
      <p class="eyebrow">Full Spa Day</p>
      <p class="pkg-price">$450<span>a $530 value &middot; save $80</span></p>
      <p class="pkg-time">About 5 hours</p>
      <ul class="pkg-list">
        <li>90 Minute Massage</li>
        <li>European Facial</li>
        <li>Spa Manicure</li>
        <li>Spa Pedicure</li>
        <li>Wash &amp; Blowout</li>
        <li>Brow Wax</li>
      </ul>
      <p class="pkg-desc">The Classic Spa Day with a longer massage and brows done &mdash; the whole day, head to toe, at the biggest saving on a single-guest package.</p>
      <a class="btn btn-primary" href="#book" data-blvd-path="/cart/menu/Packages/p_4fe93157-a423-448f-b6c8-281520f17191" data-blvd-type="PACKAGE">Buy the Full Spa Day</a>
    </div>
    <div class="pkg">
      <p class="eyebrow">For Two</p>
      <p class="pkg-price">$550<span>a $670 value &middot; save $120</span></p>
      <p class="pkg-time">About 3&frac12; hours, side by side</p>
      <ul class="pkg-list">
        <li>Two 60 Minute Massages</li>
        <li>Two European Facials</li>
        <li>Two Spa Pedicures</li>
      </ul>
      <p class="pkg-desc">Couples, mother and daughter, best friends, the bride and her maid of honor &mdash; the same day, together, at $275 a person.</p>
      <a class="btn btn-primary" href="#book" data-blvd-path="/cart/menu/Packages/p_58a5977c-5af7-444e-aa97-b0af550f93ca" data-blvd-type="PACKAGE">Buy For Two</a>
    </div>
  </div>
  <p class="pkg-foot">Every package prices well below its &agrave; la carte total. Swap a service or add on &mdash; the front desk will price it. Gifting a spa day? Packages are the most-loved <a href="/gift-cards/">gift cards</a> we sell.</p>
</section>
""",
 kw="Spa Day Packages in Poughkeepsie, NY",
 faq=[("How long does a spa package take?","The Classic Spa Day runs about four hours, the Full Spa Day about five, and For Two about three and a half with both of you in treatment at the same time — we'll confirm exact timing when you book."),
      ("Can I customize a package?","Yes. Tiers are starting points; swap services or add on and the front desk will price it for you."),
      ("Are packages good gifts?","The best. A packaged spa day is the most-loved gift card we sell — see our gift cards page.")]))

# ---------------------------------------------------------------- memberships
PAGES.append(dict(path="memberships",nav="Memberships",service="Spa Memberships",
 kw="Spa &amp; Salon Memberships in Poughkeepsie, NY",
 faq=[("Is there a contract or startup fee?","No. Omorfia memberships are month to month with no startup fee, no cancellation fee and no contract."),
      ("How do I cancel?","Call Stavros directly at (845) 694-4952 and it's done — no questions asked."),
      ("What else do members get?","Beyond the monthly service, every club includes an unlimited 10% off all other salon and spa services and special member pricing on products."),
      ("Does the membership work with every provider?","Memberships are applicable with participating service providers — ask the front desk when you book.")],
 title="Spa Memberships in Poughkeepsie, NY | Omorfia Salon & Day Spa",
 desc="Omorfia memberships are month to month with no startup fee, no cancellation fee and no contract. Members get an unlimited 10% off all other salon and spa services plus special product pricing.",
 body="""
<section class="page-hero mem-hero">
  <p class="eyebrow">Memberships</p>
  <h1>Omorfia Member Club</h1>
  <p class="lead mem-statement">Omorfia memberships are month to month &mdash; no startup fee, no cancellation fee, no contract. Members receive an <strong>unlimited 10% off every other salon and spa service</strong>, plus special discounted pricing on products. If you ever want to cancel, call Stavros directly and it&rsquo;s done &mdash; no questions asked. That&rsquo;s the whole agreement.</p>
  <p class="mem-cta"><a class="btn btn-primary" href="#book" data-blvd-path="/cart/menu/Other Memberships" data-blvd-type="MEMBERSHIP">Become a Member</a></p>
  <p class="mem-phone">Questions? Call <a href="tel:{tel}">{phone}</a> &middot; <a href="#join" role="button" data-open="join-modal">Ask Stavros</a></p>
  <p class="mem-thanks" id="memThanks" hidden>Thank you &mdash; your request is in. Stavros will be in touch shortly to set up your membership.</p>
</section>
<section class="wrap club-wrap">
  <div class="club-head"><p class="eyebrow">Spa</p><h2>Poughkeepsie Spa Club</h2></div>
  <div class="club-grid club-grid-4">
    <div class="club">
      <p class="eyebrow">Massage Club</p>
      <p class="club-price">$100<span>/month</span></p>
      <p class="club-desc">A massage every month at $35 off &mdash; 60 minutes $100, 90 minutes $160, 120 minutes $235. Any style, chosen when you arrive.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_e3c56e3b-ccd2-44dd-86e9-1fda3300ba88" data-blvd-type="MEMBERSHIP" data-club="massage60">Join</a>
    </div>
    <div class="club">
      <p class="eyebrow">Facial Club</p>
      <p class="club-price">$100<span>/month</span></p>
      <p class="club-desc">A European Facial every month &mdash; $35 off the regular price. Other facials at the member 10% off.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_c70b58ae-7f91-464c-84c6-93c16ae236f1" data-blvd-type="MEMBERSHIP" data-club="facial">Join</a>
    </div>
    <div class="club">
      <p class="eyebrow">Mani &amp; Pedi Club</p>
      <p class="club-price">$25<span>/mo each</span></p>
      <p class="club-desc">A regular manicure or pedicure every month for $25 &mdash; take both for $50.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_5e0915c6-11be-43bd-982c-9046f5a50d07" data-blvd-type="MEMBERSHIP" data-club="manipedi">Join</a>
    </div>
    <div class="club">
      <p class="eyebrow">Brow Wax Club</p>
      <p class="club-price">$22<span>/month</span></p>
      <p class="club-desc">A brow wax every month &mdash; shaped, defined, and never overdue. $8 off the regular price.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_c9d04097-0ef6-45d1-bff9-a4e16366be4c" data-blvd-type="MEMBERSHIP" data-club="brow">Join</a>
    </div>
  </div>
  <div class="club-head club-head-2"><p class="eyebrow">Salon</p><h2>Poughkeepsie Salon Club</h2></div>
  <div class="club-grid club-grid-4">
    <div class="club">
      <p class="eyebrow">Blowout Club</p>
      <p class="club-price">$120<span>/month</span></p>
      <p class="club-desc">Four wash &amp; blowouts every month &mdash; $30 each instead of $60+.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_8391bbe4-6747-4b78-b81b-275e768b836d" data-blvd-type="MEMBERSHIP" data-club="blowout">Join</a>
    </div>
    <div class="club">
      <p class="eyebrow">Women&rsquo;s Cut Club</p>
      <p class="club-price">$45<span>/month</span></p>
      <p class="club-desc">A women&rsquo;s cut every other month &mdash; always fresh, never grown out. $25 off the regular price.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_045847b9-36df-49a4-847e-1738a5674b84" data-blvd-type="MEMBERSHIP" data-club="cut">Join</a>
    </div>
    <div class="club">
      <p class="eyebrow">Color Retouch Club</p>
      <p class="club-price">$80<span>/month</span></p>
      <p class="club-desc">A root retouch every month &mdash; regrowth handled before anyone notices. $20 off the regular price.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_284276c7-b64e-4e45-aec7-6bb3911f3831" data-blvd-type="MEMBERSHIP" data-club="retouch">Join</a>
    </div>
    <div class="club">
      <p class="eyebrow">Men&rsquo;s Cut Club</p>
      <p class="club-price">$30<span>/month</span></p>
      <p class="club-desc">A men&rsquo;s cut every month &mdash; sharp on a schedule. $25 off the regular price.</p>
      <a class="btn btn-primary club-btn" href="#book" data-blvd-path="/cart/menu/Other Memberships/p_dc15dc77-d61e-4bf6-a9d0-91ec2f217b86" data-blvd-type="MEMBERSHIP" data-club="menscut">Join</a>
    </div>
  </div>
  <p class="club-foot">Every club includes an unlimited 10% off all other salon &amp; spa services and special member pricing on products. Month to month &mdash; no startup fee, no cancellation fee, no contract. <span class="club-fine">Memberships are applicable with participating service providers only.</span></p>
</section>
<div class="tmodal" id="join-modal" role="dialog" aria-modal="true" aria-label="Become a Member" hidden>
  <div class="tm-back" data-tclose></div>
  <div class="tm-card tm-solo tm-form">
    <button class="tm-x" data-tclose aria-label="Close">&times;</button>
    <div class="tm-info">
      <p class="eyebrow">Omorfia Member Club</p>
      <h3>Become a Member</h3>
      <p class="tm-bio">Tell us who you are and which club you want. We&rsquo;ll reach out to finish setup &mdash; no contract, no startup fee.</p>
      <form class="join-form" action="https://formsubmit.co/stavros@kyriacoubeauty.com" method="POST">
        <input type="hidden" name="_subject" value="New Omorfia Member Club signup">
        <input type="hidden" name="_template" value="table">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_next" value="{next_url}">
        <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">
        <label>Full name<input type="text" name="Full Name" required autocomplete="name"></label>
        <label>Phone number<input type="tel" name="Phone" required autocomplete="tel"></label>
        <label>Email<input type="email" name="Email" required autocomplete="email"></label>
        <label>Membership type
          <select name="Membership Type" required>
            <option value="" disabled selected>Choose a club</option>
            <optgroup label="Poughkeepsie Spa Club">
            <option value="Mani &amp; Pedi Club — $25/month each" data-club="manipedi">Mani &amp; Pedi Club &mdash; $25/month each</option>
            <option value="Facial Club — European Facial, $100/month" data-club="facial">Facial Club &mdash; European Facial, $100/month</option>
            <option value="Massage Club — 60 Minute, $100/month" data-club="massage60">Massage Club &mdash; 60 Minute, $100/month</option>
            <option value="Massage Club — 90 Minute, $160/month" data-club="massage90">Massage Club &mdash; 90 Minute, $160/month</option>
            <option value="Massage Club — 120 Minute, $235/month" data-club="massage120">Massage Club &mdash; 120 Minute, $235/month</option>
            <option value="Brow Wax Club — $22/month" data-club="brow">Brow Wax Club &mdash; $22/month</option>
            </optgroup>
            <optgroup label="Poughkeepsie Salon Club">
            <option value="Blowout Club — 4 blowouts, $120/month" data-club="blowout">Blowout Club &mdash; 4 blowouts, $120/month</option>
            <option value="Color Retouch Club — $80/month" data-club="retouch">Color Retouch Club &mdash; $80/month</option>
            <option value="Women's Cut Club — $45/month" data-club="cut">Women&rsquo;s Cut Club &mdash; $45/month</option>
            <option value="Men's Cut Club — $30/month" data-club="menscut">Men&rsquo;s Cut Club &mdash; $30/month</option>
            </optgroup>
            <option value="Not sure yet — help me choose" data-club="unsure">Not sure yet &mdash; help me choose</option>
          </select>
        </label>
        <button type="submit" class="btn btn-primary">Send My Request</button>
        <p class="join-note">Month to month. No startup fee, no cancellation fee, no contract. Applicable with participating service providers only.</p>
      </form>
    </div>
  </div>
</div>
<script>
(function(){
  if(window.location.search.indexOf('joined=1')>-1){var t=document.getElementById('memThanks');if(t)t.hidden=false;}
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-club]');if(!b||b.tagName==='OPTION')return;
    var sel=document.querySelector('.join-form select');if(!sel)return;
    var opt=sel.querySelector('option[data-club="'+b.getAttribute('data-club')+'"]');
    if(opt){sel.value=opt.value;}
  });
})();
</script>
""".replace("{next_url}",DOMAIN+"/memberships/?joined=1")+MODAL_JS+faq_html([("Is there a contract or startup fee?","No. Omorfia memberships are month to month with no startup fee, no cancellation fee and no contract."),
      ("How do I cancel?","Call Stavros directly at (845) 694-4952 and it&rsquo;s done &mdash; no questions asked."),
      ("What else do members get?","Beyond the monthly service, every club includes an unlimited 10% off all other salon and spa services and special member pricing on products."),
      ("Does the membership work with every provider?","Memberships are applicable with participating service providers &mdash; ask the front desk when you book.")]),faq_done=True))

# ---------------------------------------------------------------- about
PAGES.append(dict(path="about",nav="About",
 title="About Omorfia Salon & Day Spa | Poughkeepsie, NY",
 desc="Est. 2024 — Omorfia, from the Greek word for beauty, is a locally owned salon and day spa in the former Marlene Weber building in Poughkeepsie, NY, where artistry, wellness and luxury converge.",
 body="""
<section class="wrap story">
  <div class="story-media story-slides" id="aboutSlides" aria-label="Photos of Omorfia">
    <img class="story-img" src="/images/about/a01-interior.jpg" alt="Inside Omorfia Salon &amp; Day Spa in Poughkeepsie">
  </div>
  <script>
  (function(){
    var box=document.getElementById('aboutSlides');if(!box)return;
    var aimgs=["/images/about/a01-interior.jpg","/images/about/a02-team.jpg","/images/about/a03-exterior.jpg","/images/about/a04-lobby.jpg","/images/about/a05-salon-overview.jpg","/images/about/a06-salon-floor.jpg","/images/about/a07-stavros.jpg","/images/about/a08-georgia.jpg","/images/about/a09-hugo-cut.jpg","/images/about/a10-color-service.jpg","/images/about/a11-shampoo.jpg","/images/about/a12-blowdry.jpg","/images/about/a13-massage-face.jpg","/images/about/a14-product-wall.jpg","/images/about/a15-salon-chairs.jpg","/images/about/a16-team-holiday.jpg","/images/about/a17-team-dinner.jpg","/images/about/a18-salon-dog.jpg"];
    var a=document.createElement('div'),b=document.createElement('div');
    a.className='aslide on';b.className='aslide';
    box.appendChild(a);box.appendChild(b);
    a.style.backgroundImage="url('"+aimgs[0]+"')";
    var first=box.querySelector('img');if(first)first.style.visibility='hidden';
    if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    var idx=0,front=a,back=b;
    setInterval(function(){
      if(document.hidden)return;
      idx=(idx+1)%aimgs.length;
      var im=new Image();
      im.onload=function(){back.style.backgroundImage="url('"+aimgs[idx]+"')";back.classList.add('on');front.classList.remove('on');var t=front;front=back;back=t;};
      im.src=aimgs[idx];
    },4500);
  })();
  </script>
  <div class="story-copy">
    <h1 class="eyebrow">About Omorfia &middot; Poughkeepsie&rsquo;s Salon &amp; Day Spa &middot; Est. 2024</h1>
    <p class="ph-title">Where Beauty Meets Relaxation</p>
    <p>The name <em>Omorfia</em> comes from the Greek word for beauty &mdash; and it&rsquo;s this timeless pursuit that inspires everything we do. Founded with a vision to create a sanctuary where artistry, wellness, and luxury converge, Omorfia has become a beloved destination for those who seek more than just a service.</p>
    <p>Our founders envisioned a place where clients could escape the pace of everyday life and step into a world of calm, beauty, and rejuvenation. That vision found its home in the <strong>former Marlene Weber Day Spa building</strong> on Dutchess Turnpike &mdash; a Poughkeepsie spa landmark for decades, now reimagined under new, local ownership. If you knew Marlene Weber, you know the address; Omorfia is what it has become. Today, it lives on through our dedicated team of artisans who treat every client as a canvas worthy of their finest work.</p>
    <p>From our carefully curated product lines to our serene interiors, every element of Omorfia is designed to delight the senses and nurture the soul.</p>
  </div>
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">Locally owned</p>
    <h2>Poughkeepsie, by choice</h2>
    <p>Omorfia is founder-owned and operated on Dutchess Turnpike &mdash; not a franchise, not a chain. The standards come from ownership walking the floor: hand-picked providers, superior product lines, and a front desk that welcomes you like a guest in our home. <a class="btn-link" href="/team/">Meet the team &rarr;</a></p>
  </div>
  <div>
    <p class="eyebrow">The family</p>
    <h2>Part of Kyriacou Beauty Group</h2>
    <p>Omorfia is the flagship day spa of <a href="https://kyriacoubeauty.com" rel="noopener">Kyriacou Beauty Group</a>, a Hudson Valley beauty and wellness family that also includes <a href="https://omomedspa.com" target="_blank" rel="noopener">OMO Med Spa</a> for medical aesthetics and Kyriacou Cosmetics. One standard, three doors.</p>
  </div>
</section>
""",
 faq=[("What does Omorfia mean?","Omorfia (ομορφιά) is the Greek word for beauty — the name reflects the family's Greek roots and the standard the salon is built around."),
      ("Is Omorfia the old Marlene Weber Day Spa?","Omorfia occupies the former Marlene Weber Day Spa building at 751 Dutchess Turnpike in Poughkeepsie. Marlene Weber closed; Omorfia opened in July 2024 under new, local ownership with its own team and a full salon and spa menu."),
      ("Who owns Omorfia?","Omorfia is founder-owned by the Kyriacou family and is the flagship day spa of Kyriacou Beauty Group, which also operates OMO Med Spa and Kyriacou Cosmetics."),
      ("Is Omorfia a chain?","No — it's a single, locally owned salon and day spa in Poughkeepsie, NY.")]))

# ---------------------------------------------------------------- contact
PAGES.append(dict(path="contact",nav="Contact",
 title="Contact & Directions | Omorfia Salon & Day Spa, Poughkeepsie NY",
 desc="Visit Omorfia Salon & Day Spa at 751 Dutchess Turnpike, Poughkeepsie, NY 12603. Call (845) 694-4952 or book online. Open daily 9 AM – 8 PM.",
 body="""
<section class="page-hero">
  <h1 class="eyebrow">Visit Omorfia &middot; 751 Dutchess Turnpike, Poughkeepsie, NY</h1>
  <p class="ph-title">Come slow down.</p>
  <p class="lead">We&rsquo;re on Dutchess Turnpike (Route 44) in Poughkeepsie, in the <strong>former Marlene Weber building</strong>, sharing a parking lot with <strong>Adams Fairacre Farms</strong> &mdash; look for the <strong>grey and white building</strong>. Minutes from Arlington, Vassar College and the Taconic.</p>
</section>
<section class="wrap contact-grid">
  <div>
    <p class="eyebrow">Address</p>
    <h2>751 Dutchess Turnpike<br>Poughkeepsie, NY 12603</h2>
    <p class="find-us"><strong>Finding us:</strong> pull into the Adams Fairacre Farms lot &mdash; we share it &mdash; and we&rsquo;re the grey and white building, the former Marlene Weber building. Plenty of free parking.</p>
    <p><a class="btn-link" href="{maps}" rel="noopener">Open in Google Maps &rarr;</a></p>
    <p class="serving">Serving Poughkeepsie and the Hudson Valley &mdash; Hyde Park, Wappingers Falls, LaGrange, Pleasant Valley, Fishkill, Hopewell Junction, Rhinebeck, Beacon, New Paltz and Highland.</p>
  </div>
  <div>
    <p class="eyebrow">Hours</p>
    <h2>Open Daily<br>9:00 AM &ndash; 8:00 PM</h2>
    <p class="menu-note" style="margin-top:8px">Seven days a week &mdash; Sundays and evenings included.</p>
    <p class="menu-note">Holiday hours are posted on our Google listing and Instagram.</p>
  </div>
  <div>
    <p class="eyebrow">Reach us</p>
    <h2><a href="tel:{tel}">{phone}</a></h2>
    <p class="contact-email"><a href="mailto:Stavros@kyriacoubeauty.com">Stavros@kyriacoubeauty.com</a></p>
    <p><a class="btn btn-primary" href="{book}">Book Appointment</a></p>
  </div>
</section>
""".replace("{maps}",MAPS_URL),
 faq=[("Is there parking?","Yes — we share the Adams Fairacre Farms parking lot, so there's plenty of free parking. We're the grey and white building right there in the lot."),
      ("Do you take walk-ins?","When the book allows, gladly — but booking online or calling ahead is the only way to guarantee a time."),
      ("What's your cancellation policy?","Life happens — just give us as much notice as you can so we can offer the time to another guest. Full policy details are shared when you book."),
      ("Which areas do you serve?","Guests come from across the Hudson Valley — Poughkeepsie, Hyde Park, Wappingers Falls, LaGrange, Pleasant Valley, Fishkill, Hopewell Junction, Rhinebeck, Beacon, New Paltz and Highland — most within a 20-minute drive on Route 44, Route 9 or the Taconic.")]))


# ---------------------------------------------------------------- long-tail pages
# Each targets one high-intent search competitors don't have a page for. Copy stays inside
# what the menu actually offers; prices are the live menu rows.
S = "/images/slides/s%02d.jpg"

PAGES.append(topic_page("japanese-head-spa","Japanese Head Spa","Japanese Head Spa","hair",
 "Japanese Head Spa in Poughkeepsie, NY | Hudson Valley | Omorfia",
 "Japanese head spa treatments in Poughkeepsie, NY — 60-minute scalp rituals from $75 at Omorfia Salon & Day Spa. Cleanse, scalp massage, conditioning and an optional facial. Book online, open 7 days.",
 "Japanese Head Spa in Poughkeepsie, NY &mdash; Hudson Valley",
 "The scalp ritual everyone is talking about.",
 "A Japanese head spa is a meditative, hour-long treatment for the scalp &mdash; deep cleanse, long massage, conditioning &mdash; that leaves hair lighter, shinier and your whole nervous system quieter. Omorfia offers it in Poughkeepsie, seven days a week.",
 [("What a Japanese head spa actually is",[
   "Think of it as a facial for your scalp. The ritual starts with a scalp analysis and a deep cleanse that lifts product, oil and mineral buildup from the follicles. Then comes the part guests come back for: an extended scalp, neck and shoulder massage, performed slowly with warm water and conditioning treatments working into the hair. It ends with a finish and blowout so you leave presentable, not dripping.",
   "Scalp care is the foundation of healthy hair. A clean, stimulated scalp grows stronger hair, holds color better and simply feels different &mdash; most guests describe the hour as the most relaxed they have been in months."]),
  ("Three ways to book it at Omorfia",[
   "The <strong>Japanese Head Spa Conditioning Treatment (60 minutes, $150)</strong> is the full ritual: cleanse, massage and a conditioning treatment chosen for your hair. The <strong>Head Spa Facial Treatment (60 minutes, $150)</strong> pairs the scalp ritual with facial care, so face and scalp are treated in the same calm hour. Short on time? The <strong>Express Japanese Head Spa ($75)</strong> condenses the signature steps into a shorter visit.",
   "Any of the three can be added to a cut, color or blowout in the same appointment &mdash; book the head spa first and your stylist takes it from there."]),
  ("Why Omorfia for a head spa in the Hudson Valley",[
   "Head spas are still rare outside New York City. Omorfia brings the treatment to Dutchess County inside a full salon and day spa, so the scalp ritual can roll straight into color, a blowout, a massage or a facial under one roof. We are on Dutchess Turnpike in Poughkeepsie with free parking, open seven days including Sundays."])],
 [("Head Spa",[
   ("Japanese Head Spa Conditioning Treatment (60 Min)","$150+","A meditative scalp ritual &mdash; cleanse, massage, and condition."),
   ("Japanese Head Spa Facial Treatment (60 Min)","$150+","The head spa ritual, paired with facial care."),
   ("Express Japanese Head Spa","$75+","The signature ritual, condensed.")])],
 [("How long does a Japanese head spa take?","The full conditioning or facial treatment runs about 60 minutes; the express version is shorter. Add time if you're pairing it with a cut, color or blowout."),
  ("Who is a head spa for?","Anyone — it's especially loved by guests with dry or itchy scalps, product buildup, oily roots, color-treated hair, or simply a stressful week. It is gentle enough to repeat monthly."),
  ("Will my hair be wet when I leave?","No — every head spa finishes with a blow dry, so you leave styled."),
  ("Can I combine it with color?","Yes. A head spa before color gives a clean canvas; many guests book head spa + blowout or head spa + color in one visit."),
  ("Is a head spa the same as a scalp treatment?","A scalp treatment ($35) is a quick exfoliating add-on to another service. The Japanese head spa is a full, dedicated ritual with an extended massage — a different experience entirely.")],
 S%9, [("/hair/","Hair Salon Menu"),("/facials/","Facials"),("/massage/","Massage"),("/packages/","Spa Packages")], cta="Book a Head Spa"))

PAGES.append(topic_page("couples-massage","Couples Massage","Couples Massage","massage",
 "Couples Massage in Poughkeepsie, NY | Side-by-Side Spa Day | Omorfia",
 "Couples massage in Poughkeepsie, NY — two therapists, side by side, 60, 90 or 120 minutes from $135 each. Or book the For Two spa package with massages, facials and pedicures. Open 7 days.",
 "Couples Massage in Poughkeepsie, NY",
 "Side by side. Phones off.",
 "Two therapists, two tables, the same quiet room &mdash; a couples massage at Omorfia is the simplest way to spend an hour together that neither of you has to plan. Book 60, 90 or 120 minutes and choose Swedish, deep tissue or hot stone when you arrive.",
 [("How a couples massage works here",[
   "Book two massages for the same start time and tell the front desk it's a couples booking &mdash; we pair you with two therapists and set you up side by side. Each of you chooses your own style and pressure once you're on the table, so one of you can go deep tissue while the other melts into Swedish. You pay for time, not type: the same price for any style.",
   "Hot stones, amethyst crystals, Reiki or aromatherapy can be added to either table. Arrive a few minutes early, hydrate, and leave the rest to us."]),
  ("Make it a whole afternoon",[
   "The <strong>For Two spa package ($550, a $670 value)</strong> is our most-booked couples experience: two 60-minute massages, two European facials and two spa pedicures, about three and a half hours together for $275 a person. It's the anniversary, birthday, mother-and-daughter or best-friend plan that requires zero decisions.",
   "Couples massage is also our most-gifted service &mdash; a <a href=\"/gift-cards/\">gift card</a> loaded for two massages or the For Two package arrives by email in a minute."]),
  ("Poughkeepsie's day spa for two",[
   "We're on Dutchess Turnpike with free parking, minutes from Arlington, Vassar and the Taconic, and open seven days a week including Sundays and evenings &mdash; so a couples massage fits a weekend, a date night or a day off without rearranging anything."])],
 [("Massage &middot; Per person, choose your style when you arrive",[
   ("60 Minute Massage","$135","The classic hour &mdash; any style, chosen when you arrive.","$100"),
   ("90 Minute Massage","$195","Full body plus real time on problem areas.","$160"),
   ("120 Minute Massage","$270","Two unhurried hours, head to toe.","$235")]),
  ("For Two Package",[
   ("For Two &mdash; Two Massages, Two Facials, Two Pedicures","$550","About 3&frac12; hours side by side &mdash; a $670 value.")]),
  ("Enhancements",[
   ("Hot Stones","$30","Add heated stones to either massage."),
   ("Aromatherapy","$10","Essential oils chosen for your session.")])],
 [("Do we have to pick the same massage?","No — each of you chooses your own style and pressure with your therapist. Same price for Swedish, deep tissue or hot stone."),
  ("How do I book a couples massage?","Book two massages for the same time online, or call (845) 694-4952 and say it's for a couple — we'll pair the therapists and the room."),
  ("Can we do more than a massage?","Yes — the For Two package adds facials and pedicures, or the front desk can build a custom day for two."),
  ("Is a couples massage a good gift?","It's our most-gifted service. Gift cards work for any amount, a specific service or the For Two package."),
  ("Are you open on Sundays?","Yes — seven days a week, 9 AM to 8 PM.")],
 S%13, [("/massage/","Massage Menu"),("/packages/","For Two Package"),("/gift-cards/","Gift Cards"),("/deep-tissue-massage/","Deep Tissue")], cta="Book for Two"))

PAGES.append(topic_page("deep-tissue-massage","Deep Tissue Massage","Deep Tissue Massage","massage",
 "Deep Tissue Massage in Poughkeepsie, NY | Omorfia Day Spa",
 "Deep tissue massage in Poughkeepsie, NY from licensed therapists — 60, 90 or 120 minutes from $135, hot stone add-on, open 7 days including Sundays. Same price as Swedish. Book online at Omorfia.",
 "Deep Tissue Massage in Poughkeepsie, NY",
 "For the knots that have overstayed their welcome.",
 "Slow, focused pressure into the muscle layers that a lighter massage never reaches &mdash; for desk shoulders, runner's calves, lifting backs and the tension that follows you home. Licensed therapists, quiet rooms, and the same price as any other style.",
 [("What deep tissue is (and isn't)",[
   "Deep tissue massage works the deeper layers of muscle and connective tissue with slower strokes and sustained pressure. It's the right call for chronic tightness, postural strain and recovery from training. It isn't meant to hurt: a good deep tissue session sits at the edge of discomfort, never past it, and your therapist adjusts pressure the moment you ask.",
   "At Omorfia you book the time, not the type. Start deep, finish Swedish, or focus the whole session on one stubborn area &mdash; it's decided with your therapist on the table, and the price doesn't change."]),
  ("Which length to book",[
   "<strong>60 minutes</strong> covers full-body maintenance with real work on one or two problem areas. <strong>90 minutes</strong> is the sweet spot for deep tissue &mdash; enough time to warm the tissue properly before going deep, without shortchanging the rest of you. <strong>120 minutes</strong> is the full reset for anyone carrying a season's worth of tension.",
   "Add <strong>hot stones ($30)</strong> to loosen muscle before deeper work, or <strong>Reiki ($30)</strong> if you want the nervous system settled along with the muscle."]),
  ("Make it monthly",[
   "The <a href=\"/memberships/\">Massage Club</a> brings a monthly massage to $100 for 60 minutes, $160 for 90 and $235 for 120 &mdash; month to month, no contract, no startup fee, plus 10% off everything else in the salon and spa."])],
 [("Massage &middot; Choose your style when you arrive",[
   ("60 Minute Massage","$135","Deep tissue, Swedish, hot stone or a blend.","$100"),
   ("90 Minute Massage","$195","Real time on problem areas without rushing the rest.","$160"),
   ("120 Minute Massage","$270","The full reset.","$235")]),
  ("Enhancements",[
   ("Hot Stones","$30","Heat to loosen muscle before deeper work."),
   ("Reiki Energy Work","$30","Add energy balancing to your massage."),
   ("Aromatherapy","$10","Essential oils chosen for your session.")])],
 [("Does deep tissue massage hurt?","It shouldn't. Expect firm, focused pressure and some intensity on tight spots, but tell your therapist if anything crosses from 'good pain' to pain — pressure is adjusted instantly."),
  ("Is deep tissue more expensive than Swedish?","No. At Omorfia you pay for the length of the session, not the style."),
  ("How often should I get deep tissue?","For chronic tension, every two to four weeks works well; many guests use the Massage Club to keep it monthly."),
  ("Will I be sore afterward?","Some mild soreness for a day is normal after deep work. Hydrate, move gently, and it passes."),
  ("Can I get one on a Sunday evening?","Yes — we're open seven days, 9 AM to 8 PM.")],
 S%14, [("/massage/","Massage Menu"),("/couples-massage/","Couples Massage"),("/prenatal-massage/","Prenatal Massage"),("/memberships/","Massage Club")]))

PAGES.append(topic_page("prenatal-massage","Prenatal Massage","Prenatal Massage","massage",
 "Prenatal Massage in Poughkeepsie, NY | Pregnancy Massage | Omorfia",
 "Prenatal massage in Poughkeepsie, NY — $140 pregnancy massage with supported side-lying positioning from licensed therapists at Omorfia Day Spa. Open 7 days, free parking, book online.",
 "Prenatal Massage in Poughkeepsie, NY",
 "Comfort for the body doing the most work.",
 "A pregnancy massage designed around you: supported side-lying positioning, pressure chosen for the trimester, and a therapist who knows where the aches live &mdash; low back, hips, feet and the shoulders carrying everything else.",
 [("What to expect from a prenatal massage",[
   "Prenatal massage uses the techniques of a classic relaxation massage adapted for pregnancy. You're positioned on your side with pillows and bolsters for full support, and the work focuses on the areas that take the strain: the lower back and hips, the legs and feet, the neck and shoulders. Pressure stays gentle to moderate, and the deep abdominal work and certain pressure points used in other massages are avoided.",
   "Most guests book from the second trimester onward. If you have a high-risk pregnancy or any medical concerns, check with your provider first &mdash; and tell your therapist how you're feeling on the day."]),
  ("Why guests choose Omorfia",[
   "Quiet treatment rooms, licensed therapists, and a 60-minute <strong>Pre-Natal Massage ($140)</strong> that's never rushed. We're open seven days, including Sundays and evenings, with free parking right at the door on Dutchess Turnpike &mdash; small things that matter a lot in the third trimester.",
   "Pair it with a <a href=\"/nails/\">spa pedicure</a> in the same visit, or let someone gift it: prenatal massage is one of the kindest <a href=\"/gift-cards/\">gift cards</a> on our books."])],
 [("Prenatal",[
   ("Pre-Natal Massage","$140","Safe, supported comfort for moms-to-be."),
   ("Aromatherapy","$10","Gentle essential oils, chosen with you.")])],
 [("When in pregnancy can I get a massage?","Most guests book from the second trimester on. If you're in the first trimester or have a high-risk pregnancy, check with your provider before booking."),
  ("How am I positioned?","On your side, fully supported with pillows and bolsters — never face-down."),
  ("Is the pressure lighter?","Pressure is gentle to moderate and adjusted to how you feel on the day. Tell your therapist anything — that's the whole point."),
  ("Can I book one as a gift?","Yes — gift cards can be loaded for a prenatal massage specifically."),
  ("Do you have parking?","Yes, free parking in our lot at 751 Dutchess Turnpike.")],
 S%15, [("/massage/","Massage Menu"),("/nails/","Spa Pedicure"),("/gift-cards/","Gift Cards"),("/facials/","Facials")]))

PAGES.append(topic_page("balayage","Balayage","Balayage","hair",
 "Balayage in Poughkeepsie, NY | Hand-Painted Highlights | Omorfia Salon",
 "Balayage in Poughkeepsie, NY — hand-painted, lived-in color from $200 partial / $320 full, baby lights, face framing and glosses at Omorfia Salon & Day Spa. Free balayage consultation. Open 7 days.",
 "Balayage in Poughkeepsie, NY",
 "Color that looks like you were born lucky.",
 "Hand-painted, sun-kissed dimension that grows out softly for months &mdash; no harsh lines, no six-week root panic. Partial, full, baby lights and face framing, with a complimentary consultation to map placement and tone before anyone picks up a brush.",
 [("Balayage vs. highlights: which do you want?",[
   "<strong>Balayage</strong> is hand-painted onto the surface of the hair, concentrating lightness toward the ends with a soft, diffused root &mdash; the lived-in look that grows out gracefully. <strong>Foil highlights</strong> lift from closer to the root in uniform sections for brighter, more consistent lightness. <strong>Baby lights</strong> are ultra-fine foils for a natural, sun-kissed finish. Many of our best results blend them: foils for brightness, balayage for softness.",
   "Not sure? The <strong>balayage consultation is complimentary</strong>. Bring photos; your colorist maps placement, tone and realistic timing for your starting color."]),
  ("What a balayage appointment includes",[
   "Partial balayage ($200+) paints the top layers and face frame for dimension where it shows. Full balayage ($320+) is hand-painted throughout for the complete lived-in look. Both finish with a <strong>toner or glaze</strong> to land the exact tone &mdash; beige, honey, ash, copper &mdash; and a styled blowout.",
   "Color-treated hair deserves care: add an <strong>Olaplex bond treatment ($50)</strong> or a conditioning mask during your service, and book a toner or glaze ($45) between full appointments to keep brass away and shine high."]),
  ("Colorists who ask first",[
   "Our senior and master colorists work in a salon where color is a conversation, not a menu number. Tell us the goal, the maintenance you'll actually do, and what you loved and hated last time &mdash; then we'll build the plan. Open seven days in Poughkeepsie, with free parking."])],
 [("Balayage",[
   ("Balayage Consultation","Complimentary","Map placement and tone before your appointment."),
   ("Partial Balayage","$200+","Hand-painted dimension through the top layers."),
   ("Full Balayage","$320+","Full hand-painted, lived-in color."),
   ("Face Framing Highlight","$80+","Brightness right where it catches the light."),
   ("Baby Lights","$200+","Ultra-fine foils for a sun-kissed, natural finish.")]),
  ("Finish &amp; Care",[
   ("Toner / Glaze","$45+","Neutralize brass and add gloss between services."),
   ("Root Smudge","$35+","Soften the line between roots and color."),
   ("Olaplex Hair Treatment","$50+","Bond-rebuilding repair for color-treated hair.")])],
 [("How long does balayage take?","Plan on two to four hours depending on length, density and how much lift you need; your colorist confirms timing at the consultation."),
  ("How often do I need to come back?","That's the beauty of it — most guests refresh every three to five months, with a toner or glaze in between to keep the tone fresh."),
  ("Can balayage work on dark hair?","Yes. Dark hair may take more than one session to reach very light tones safely; your colorist will be honest about what's achievable in one visit."),
  ("Why are prices 'starting at'?","Length, density and your starting color change the product and time involved. You'll have an exact quote before the service begins."),
  ("Is the consultation really free?","Yes — balayage, vivid, keratin and extension consultations are all complimentary.")],
 S%10, [("/hair/","Full Hair Menu"),("/hair-extensions/","Hair Extensions"),("/keratin-treatment/","Keratin Smoothing"),("/memberships/","Color Retouch Club")]))

PAGES.append(topic_page("hair-extensions","Hair Extensions","Hair Extensions","hair",
 "Hair Extensions in Poughkeepsie, NY | K-Tip, I-Tip, Tape-In & Weft | Omorfia",
 "Hair extensions in Poughkeepsie, NY — K-tip, I-tip, tape-in and hand-tied weft extensions from $125 with a free consultation and an in-house extension specialist at Omorfia Salon & Day Spa.",
 "Hair Extensions in Poughkeepsie, NY",
 "Length and fullness that pass the touch test.",
 "K-tip, I-tip, tape-in and weft extensions, matched to your color and installed by an extension specialist &mdash; so they move, part and feel like your own hair. The consultation is complimentary.",
 [("Four methods, one honest consultation",[
   "<strong>K-Tip ($175+)</strong>: keratin-bonded strands for the most seamless, long-wearing result. <strong>I-Tip ($150+)</strong>: bead-set strands with no heat and no glue &mdash; gentle on fine hair. <strong>Tape-In ($125+)</strong>: fast, flat, comfortable panels, ideal for a first set. <strong>Weft ($300+)</strong>: a full sewn-in row for maximum fullness in one install.",
   "Which one is right depends on your hair's density, your lifestyle and how much maintenance you'll actually do. That's what the <strong>complimentary extension consultation</strong> is for: we match the method, length and color before you commit to anything."]),
  ("Living with extensions",[
   "Extensions need their own care &mdash; a dedicated brush, sleeping in a loose braid, and professional removal when the time comes. We offer an <strong>extension blowdry ($70+)</strong> styled around your set and <strong>safe extension removal ($100+)</strong> that protects your natural hair. Move-ups and maintenance are scheduled with your specialist at install."]),
  ("Extensions for the big day",[
   "Bridal updos, prom styles and event hair all photograph better with a little extra length and density. Book extensions a few weeks before a <a href=\"/wedding/\">wedding</a> or <a href=\"/prom-hair-and-makeup/\">prom</a> so they settle in before the trial."])],
 [("Extensions",[
   ("Extension Consultation","Complimentary","Match method, length, and color to your goals."),
   ("K-Tip Extensions","$175+","Keratin-bonded strands for seamless length."),
   ("I-Tip Extensions","$150+","Bead-set strands &mdash; no heat, no glue."),
   ("Tape-In Extensions","$125+","Fast, flat, comfortable panels of length."),
   ("Weft Extensions","$300+","A full sewn-in row for maximum fullness."),
   ("Extension Blowdry","$70+","A blowout styled around your extensions."),
   ("Extension Removal","$100+","Safe removal that protects your natural hair.")])],
 [("Which extension method is best?","It depends on your hair's density and your routine — tape-ins for speed and comfort, K-tips for the most seamless wear, I-tips for no heat or glue, wefts for maximum fullness. The free consultation settles it."),
  ("How long do extensions last?","Tape-ins and wefts are typically moved up every six to eight weeks; strand methods wear longer between maintenance. Your specialist sets the schedule at install."),
  ("Do prices include the hair?","Prices are starting points for installation; hair cost depends on length, color and the amount needed, and is quoted at your consultation."),
  ("Can extensions damage my hair?","Not when installed, maintained and removed professionally. Skipping maintenance or pulling them out at home is where damage happens — which is why removal is a service."),
  ("Do you color-match?","Yes — matching to your color (or to a planned balayage) is part of the consultation.")],
 S%11, [("/hair/","Full Hair Menu"),("/balayage/","Balayage"),("/wedding/","Bridal Hair"),("/prom-hair-and-makeup/","Prom Hair")]))

PAGES.append(topic_page("keratin-treatment","Keratin Smoothing","Keratin Treatment","hair",
 "Keratin Treatment in Poughkeepsie, NY | Smoothing & Frizz Control | Omorfia",
 "Keratin smoothing treatments in Poughkeepsie, NY — 30-day keratin from $150, 4-month keratin relaxing from $350, Magic Sleek and B Blowout at Omorfia Salon & Day Spa. Free keratin consultation.",
 "Keratin Treatment in Poughkeepsie, NY",
 "Frizz, handled for a season.",
 "Keratin smoothing treatments that cut blow-dry time in half and keep humidity from having an opinion about your hair &mdash; from a 30-day reset to a four-month relaxing treatment. The consultation is complimentary.",
 [("Choosing your smoothing treatment",[
   "<strong>Keratin Smoothing Treatment, 30-day ($150+)</strong>: a frizz-taming reset that lasts about a month &mdash; perfect before a trip, a wedding or summer. <strong>Keratin Relaxing Treatment, 4-month ($350+)</strong>: deep smoothing that holds for a season and makes daily styling almost unnecessary. <strong>Magic Sleek ($300+)</strong>: a salon-grade straightening system for lasting sleekness. <strong>B Blowout ($250+)</strong>: a professional smoothing blowout for long-wear frizz control with more movement left in.",
   "A keratin treatment smooths the cuticle and seals in a protein layer; it doesn't bleach or permanently change your curl pattern, and results soften gradually rather than growing out with a line. The <strong>keratin consultation is complimentary</strong> and the right place to talk through texture, color history and the finish you want."]),
  ("Before and after",[
   "Arrive with clean, product-free hair if you can. Afterward, use sulfate-free shampoo and skip tight ponytails for the first days as your stylist advises &mdash; small habits that stretch the result. Color can usually be scheduled around a keratin treatment; ask at the consultation and we'll sequence the two."]),
  ("Hudson Valley humidity, solved",[
   "Our stylists do smoothing treatments year-round in Poughkeepsie, from June humidity to winter static. Open seven days, free parking, and a full salon menu if you want a cut or gloss in the same visit."])],
 [("Texture &amp; Smoothing",[
   ("Keratin Consultation","Complimentary","Find the right smoothing treatment for your hair."),
   ("Keratin Smoothing Treatment (30-Day)","$150+","A frizz-taming reset that lasts about a month."),
   ("Keratin Relaxing Treatment (4-Month)","$350+","Deep smoothing that holds for a season."),
   ("Magic Sleek Treatment","$300+","Salon-grade straightening system for lasting sleekness."),
   ("B Blowout","$250+","Professional smoothing blowout for long-wear frizz control.")]),
  ("Care",[
   ("Amika Anti-Frizz Treatment","$20+","A quick humidity shield for smoother wear."),
   ("Kerasilk Recovery Mask","$50+","Luxury smoothing mask for stressed strands.")])],
 [("How long does a keratin treatment last?","The 30-day treatment lasts about a month; the relaxing treatment holds around four months. Results fade gradually, not with a regrowth line."),
  ("Will it make my hair straight?","It smooths and reduces frizz and volume; how straight depends on the treatment you choose and your texture. Magic Sleek is the most straightening option."),
  ("Can I color my hair and get keratin?","Usually yes — your stylist will sequence them at the consultation."),
  ("How long is the appointment?","Plan two to three hours depending on length and density."),
  ("Is the consultation free?","Yes — keratin consultations are complimentary.")],
 S%12, [("/hair/","Full Hair Menu"),("/balayage/","Balayage"),("/japanese-head-spa/","Japanese Head Spa"),("/memberships/","Blowout Club")]))

PAGES.append(topic_page("microblading","Microblading","Microblading","lashes-brows",
 "Microblading in Poughkeepsie, NY | Brow Tattoo & Fills | Omorfia",
 "Microblading in Poughkeepsie, NY — hair-stroke brow tattooing $450 with fills at $250, plus brow lamination, tint and wax at Omorfia Salon & Day Spa. Open 7 days, book online.",
 "Microblading in Poughkeepsie, NY",
 "Brows you wake up with.",
 "Hair-stroke microblading that fills, shapes and defines brows naturally &mdash; and stays put for a year or more. For a softer commitment, brow lamination, tint and shaping are on the same menu.",
 [("What microblading is",[
   "Microblading is a semi-permanent brow technique: a hand tool deposits pigment in fine, hair-like strokes along the brow to recreate the look of natural hair. It's the answer for sparse, over-plucked or uneven brows, and for anyone tired of drawing them on every morning. Results typically last twelve to eighteen months, with a fill recommended to keep the strokes crisp.",
   "Your appointment starts with mapping: shape, arch and pigment are agreed on paper and on your face before any work begins. Expect the color to look darker for the first week and soften as it heals."]),
  ("Microblading, lamination or tint?",[
   "<strong>Microblading ($450)</strong> adds hair strokes where you don't have hair. <strong>Brow lamination &amp; tint ($100)</strong> brushes your existing brows up and sets them in place for weeks &mdash; fuller, fluffier, no needles. <strong>Brow tint ($25)</strong> and a <strong>brow wax ($30)</strong> are the quick refresh. Not sure which? Book a brow wax and ask; our brow specialists will tell you honestly."]),
  ("Brows at a full day spa",[
   "Pair brows with a <a href=\"/lashes-brows/\">lash lift</a>, a <a href=\"/facials/\">facial</a> or a blowout in the same visit. Open seven days in Poughkeepsie with free parking."])],
 [("Brows",[
   ("Microblading","$450","Hair-stroke brow tattooing for natural fullness."),
   ("Microblade Fill","$250","Refresh strokes and color on existing work."),
   ("Brow Lamination &amp; Tint","$100","Brushed-up, set-in-place brows with tint."),
   ("Brow Tint","$25","Richer, fuller-looking brows in minutes."),
   ("Brow Wax","$30","Shape and define the arch.","$22/month club &mdash; a brow wax every month")])],
 [("How long does microblading last?","Twelve to eighteen months for most guests, with a fill ($250) recommended to keep the strokes crisp."),
  ("Does microblading hurt?","Most guests describe it as scratching or mild pressure; a topical numbing is applied before the work."),
  ("What's the healing like?","Brows look darker and bolder for about a week, then soften to the final shade over a few weeks. Keep them dry and skip makeup on the area as instructed."),
  ("Who shouldn't get microblading?","Pregnant or nursing guests and anyone with certain skin or medical conditions should wait; tell us your history when you book."),
  ("Is a touch-up included?","Fills are booked as a separate service ($250) when the strokes begin to soften.")],
 S%16, [("/lashes-brows/","Lashes &amp; Brows Menu"),("/facials/","Facials &amp; Waxing"),("/makeup/","Makeup"),("/memberships/","Brow Wax Club")]))

PAGES.append(topic_page("brazilian-wax","Waxing","Waxing","facials",
 "Brazilian Wax & Body Waxing in Poughkeepsie, NY | Omorfia Day Spa",
 "Brazilian wax $80, bikini $50, legs, arms, back, chest and face waxing in Poughkeepsie, NY — licensed estheticians, private rooms, open 7 days at Omorfia Salon & Day Spa.",
 "Brazilian Wax &amp; Body Waxing in Poughkeepsie, NY",
 "Smooth, quick, no drama.",
 "Brazilian, bikini, legs, arms, back, chest and face &mdash; waxing by licensed estheticians in private treatment rooms, with results that outlast shaving by weeks. Full price list below.",
 [("Waxing done properly",[
   "Every wax at Omorfia happens in a private room with a licensed esthetician, fresh supplies for each guest and a pace that doesn't feel rushed. A <strong>Brazilian ($80)</strong> removes everything or nearly everything &mdash; your call. A <strong>French bikini ($70)</strong> goes higher and deeper than the classic <strong>bikini ($50)</strong>. Legs, arms, underarms, back and chest round out the body menu; brow, lip, chin and full-face waxing handle the rest.",
   "Hair should be about a quarter inch long for the wax to grip. Exfoliate the day before, skip lotions and oils the day of, and tell your esthetician if you use retinoids or have had recent sun."]),
  ("How often, and how to keep it smooth",[
   "Most guests return every four to six weeks; hair grows back finer and sparser over time. The <a href=\"/memberships/\">Brow Wax Club ($22/month)</a> keeps brows on schedule, and 10% member pricing applies to every other wax.",
   "Waxing before a <a href=\"/wedding/\">wedding</a>, <a href=\"/tanning/\">spray tan</a> or vacation? Book the wax a day or two ahead so the skin settles."])],
 [("Body Waxing",[
   ("Brazilian Wax","$80","Everything, or nearly everything &mdash; your call."),
   ("French Bikini Wax","$70","Higher and deeper than the classic bikini."),
   ("Bikini Wax","$50","Clean lines along the bikini edge."),
   ("Full Leg Wax","$84","Hip to ankle, completely smooth."),
   ("Half Leg Wax","$58","Knee down &mdash; the sandal essential."),
   ("Underarm Wax","$37","Smooth results that outlast shaving."),
   ("Full Arm Wax","$58","Shoulder to wrist."),
   ("Half Arm Wax","$47","Elbow down, silky smooth."),
   ("Back Wax","$74","Full back, shoulder to waist."),
   ("Chest Wax","$74","Full chest, done properly.")]),
  ("Face Waxing",[
   ("Brow Wax","$30","Shape and define the arch.","$22/month club &mdash; a brow wax every month"),
   ("Lip Wax","$21","Quick, clean upper-lip removal."),
   ("Neck Wax","$23","Clean up the neckline."),
   ("Full Face Wax","$60","Brow, lip, chin, and cheeks in one visit.")])],
 [("How long should hair be for waxing?","About a quarter inch — roughly two to three weeks of growth after shaving."),
  ("Does a Brazilian wax hurt?","The first one is the most sensitive; it gets easier each visit as hair grows back finer. Our estheticians work quickly and talk you through it."),
  ("How long do results last?","Three to six weeks for most guests, depending on your hair growth."),
  ("Can I wax before a spray tan?","Yes — wax a day or two before your tan so the skin settles first."),
  ("Do you wax men?","Yes — back, chest, brows and more are on the menu for everyone.")],
 S%17, [("/facials/","Facials &amp; Waxing Menu"),("/tanning/","Spray Tanning"),("/memberships/","Brow Wax Club"),("/packages/","Spa Packages")], cta="Book a Wax"))

PAGES.append(topic_page("prom-hair-and-makeup","Prom Hair &amp; Makeup","Prom Hair and Makeup","makeup",
 "Prom Hair & Makeup in Poughkeepsie, NY | Updos, Lashes, Nails & Spray Tan | Omorfia",
 "Prom hair and makeup in Poughkeepsie, NY — updos from $115, half-up styles $70, full makeup $100, lashes, nails and a spray tan under one roof at Omorfia Salon & Day Spa. Book early for prom weekends.",
 "Prom Hair &amp; Makeup in Poughkeepsie, NY",
 "The night deserves the full treatment.",
 "Updos, waves, half-up styles, camera-ready makeup, lashes, nails and a sunless glow &mdash; prom gets the bridal treatment at Omorfia, with the whole friend group styled on one timeline under one roof.",
 [("Prom, the way we do it",[
   "Book hair and makeup back to back and your look is finished in a single sitting: a <strong>full updo ($115+)</strong> or <strong>half-up style ($70+)</strong>, <strong>hot-tool curls or waves ($30+)</strong>, then <strong>full-face makeup ($100)</strong> with <strong>strip lashes ($15)</strong> or <strong>clusters ($40)</strong> for drama that lasts past the last song. A <strong>bang trim</strong> or <strong>toner</strong> the week before keeps everything crisp.",
   "Bring photos of the dress and the look you love. Our stylists and makeup artists work with your hair type and your face, not a one-size template."]),
  ("Nails, glow and the group",[
   "<strong>Gel manicures ($45)</strong> and pedicures survive the night. A <strong>Show Stopper spray tan ($40 upper body / $80 full)</strong> booked one to two days before reads sun-kissed in photos. And because Omorfia is a full salon and day spa, your friends can all book the same afternoon and get ready together.",
   "Prom weekends in Dutchess County fill fast &mdash; book as soon as you have the date, and ask about group timelines for parties of four or more."]),
  ("Parents: we see you too",[
   "A blowout, a <a href=\"/facials/\">facial</a> or a <a href=\"/massage/\">massage</a> while the getting-ready happens is a very reasonable use of the afternoon."])],
 [("Prom Hair",[
   ("Updo","$115+","Full formal styling for weddings, proms, and galas."),
   ("Half Up / Half Down","$70+","Polished event styling with movement left in."),
   ("Hot Tool Finish","$30+","Curls or waves set with a hot tool."),
   ("Wash &amp; Blow Dry","$60+","Shampoo, condition, and a polished blowout."),
   ("Braiding","$60+","From one statement braid to a fully braided style.")]),
  ("Prom Makeup &amp; Lashes",[
   ("Traditional Application","$100","Full-face artistry for events and nights out."),
   ("Strip Lashes","$15","Applied with any makeup service."),
   ("Lash Clusters","$40","Buildable clusters for tailored drama.")]),
  ("Nails &amp; Glow",[
   ("Gel Manicure","$45","Chip-resistant color cured to a two-week shine."),
   ("Show Stopper Full Body Glow","$80","Head-to-toe sunless color, matched to your skin tone."),
   ("Show Stopper Upper Body Glow","$40","Face, arms, and shoulders &mdash; camera-ready.")])],
 [("How far ahead should I book for prom?","As soon as you have the date — prom Saturdays in April, May and June book out weeks ahead."),
  ("Can my friends and I get ready together?","Yes. Tell us the group size when you book and we'll schedule hair, makeup and nails on one timeline."),
  ("Should I wash my hair before an updo?","Day-old, product-free hair usually holds an updo best; your stylist will tell you what works for your hair when you book."),
  ("Do you do a trial for prom?","Trials are available for hair or makeup if you want to lock the look — ask when booking."),
  ("When should I get my spray tan?","One to two days before, after any waxing, so the color settles.")],
 S%18, [("/makeup/","Makeup Menu"),("/hair/","Hair Menu"),("/tanning/","Spray Tan"),("/nails/","Nails")], cta="Book Prom"))

# ---------------------------------------------------------------- areas we serve
AREAS = [
 ("Hyde Park","about 10 minutes north on Route 9","Hyde Park guests come down Route 9 for Sunday massages and color — we're the closest full day spa south of the Vanderbilt and FDR sites."),
 ("Wappingers Falls","about 15 minutes south via Route 9 or the Taconic","Wappingers and Hopewell guests tend to book the long version: a 90-minute massage, a facial, nails — a package makes the drive worth it."),
 ("LaGrange","about 10 minutes east on Route 44 / Route 55","LaGrangeville and Freedom Plains are straight down Dutchess Turnpike — the easiest drive on this list."),
 ("Pleasant Valley","about 10 minutes east on Route 44","Route 44 brings Pleasant Valley and Salt Point right to our lot — the Adams Fairacre Farms lot, to be exact."),
 ("Fishkill","about 20 minutes south on Route 9","Fishkill and Beacon guests book us for the things a chain doesn't do: Japanese head spa, balayage, bridal parties, full spa days."),
 ("Hopewell Junction","about 20 minutes via the Taconic","Taconic to Route 55 to Route 44 — twenty minutes, free parking, and a seven-day schedule that fits around commuting."),
 ("Rhinebeck","about 25 minutes north on Route 9","Rhinebeck and Red Hook guests come for salon-and-spa days without resort pricing, and for Sunday appointments."),
 ("Beacon","about 25 minutes south","A spa day in Poughkeepsie pairs well with a Beacon weekend — book the For Two package and make an afternoon of it."),
 ("New Paltz","about 20 minutes across the Mid-Hudson Bridge","New Paltz, Highland and Gardiner guests cross the bridge for hair color, lashes and massage — and for a parking lot."),
 ("Highland","about 15 minutes across the bridge","Highland and Marlboro are a bridge away: over the Mid-Hudson, up Route 44, and you're here."),
]
_area_sections = "".join(
  f'<div class="area"><h3>{t}</h3><p class="area-dist">{d}</p><p>{b}</p></div>' for t,d,b in AREAS)
PAGES.append(dict(path="hudson-valley",nav="Areas We Serve",
 title="Salon & Day Spa Serving the Hudson Valley | Hyde Park, Wappingers, LaGrange & More | Omorfia",
 desc="Omorfia Salon & Day Spa in Poughkeepsie serves the whole Hudson Valley — Hyde Park, Wappingers Falls, LaGrange, Pleasant Valley, Fishkill, Hopewell Junction, Rhinebeck, Beacon, New Paltz and Highland. Directions, drive times and what to book.",
 kw="Salon &amp; Day Spa Serving the Hudson Valley",
 body="""
<section class="page-hero">
  <p class="eyebrow">Areas we serve</p>
  <h1>One address. The whole valley.</h1>
  <p class="lead">Omorfia sits on Dutchess Turnpike (Route 44) in Poughkeepsie &mdash; the former Marlene Weber Day Spa building, sharing the Adams Fairacre Farms lot &mdash; within a twenty-five-minute drive of most of Dutchess and eastern Ulster County. Here&rsquo;s how guests from each town find us, and what they tend to book.</p>
  <a class="btn btn-primary" href="{book}">Book Appointment</a>
</section>
<section class="wrap">
  <p class="eyebrow">By town</p>
  <h2>Drive times &amp; directions</h2>
  <div class="area-grid">"""+_area_sections+"""</div>
  <p class="menu-note">Drive times are typical off-peak estimates. Free parking in our lot at 751 Dutchess Turnpike, Poughkeepsie, NY 12603 &mdash; <a href=\"""" + MAPS_URL + """\" rel="noopener">open in Google Maps</a>.</p>
</section>
<section class="wrap split">
  <div>
    <p class="eyebrow">Why the drive is worth it</p>
    <h2>Everything under one roof</h2>
    <p>Hair, nails, massage, facials, waxing, lashes, spray tanning, makeup and bridal &mdash; stacked into one appointment if you like. Open seven days a week, 9 AM to 8 PM, Sundays included. <a class="btn-link" href="/packages/">See spa packages &rarr;</a></p>
  </div>
  <div>
    <p class="eyebrow">Worth knowing</p>
    <h2>Memberships travel well</h2>
    <p>Monthly massage, facial, nail and salon clubs with no contract &mdash; and 10% off everything else &mdash; make a standing drive to Poughkeepsie an easy habit. <a class="btn-link" href="/memberships/">See memberships &rarr;</a></p>
  </div>
</section>
""",
 faq=[("Where exactly is Omorfia?","751 Dutchess Turnpike (Route 44), Poughkeepsie, NY 12603 — the grey and white former Marlene Weber building sharing the Adams Fairacre Farms parking lot, minutes from Arlington and Vassar College."),
      ("Is there parking?","Yes — free parking in the lot, no garage, no meters."),
      ("Do you serve clients outside Poughkeepsie?","Most of our guests drive in from across Dutchess and Ulster counties — Hyde Park, Wappingers Falls, LaGrange, Pleasant Valley, Fishkill, Hopewell Junction, Rhinebeck, Beacon, New Paltz and Highland among them."),
      ("Do you offer on-location bridal services?","Ask during your bridal consultation — depending on the date, venue and party size we'll recommend in-salon or discuss on-location options."),
      ("Are you open weekends?","Seven days a week, 9 AM to 8 PM, including Sundays.")]))


# ---------------------------------------------------------------- full menu / price list
_SVC_ORDER = ["hair","nails","massage","facials","lashes-brows","tanning","makeup"]
_svc_pages = [next(p for p in PAGES if p["path"]==s) for s in _SVC_ORDER]
_jump = " &middot; ".join(f'<a href="#{p["path"]}">{p["nav"]}</a>' for p in _svc_pages) + ' &middot; <a href="/wedding/">Wedding &amp; Bridal</a> &middot; <a href="/packages/">Packages</a> &middot; <a href="/memberships/">Memberships</a>'
_menu_sections = "".join(
  f'<section class="wrap menu-wrap menu-all" id="{p["path"]}"><p class="eyebrow">{p["nav"]}</p><h2>{p["service"]}</h2>'
  f'{menu_html(p["groups"], "menu-"+p["path"])}'
  f'<p class="menu-note"><a class="btn-link" href="/{p["path"]}/">More about {p["nav"].lower()} &rarr;</a></p></section>'
  for p in _svc_pages)
PAGES.append(dict(path="menu",nav="Services & Prices",
 title="Salon & Spa Services & Prices | Omorfia Salon & Day Spa, Poughkeepsie NY",
 desc="Full service menu and prices for Omorfia Salon & Day Spa in Poughkeepsie, NY — hair, nails, massage, facials, waxing, lashes, brows, spray tanning and makeup. Member pricing shown. Open 7 days.",
 kw="Salon &amp; Spa Services &amp; Prices in Poughkeepsie, NY",
 body="""
<section class="page-hero">
  <p class="eyebrow">The full menu</p>
  <h1>Every service. Every price.</h1>
  <p class="lead">The complete Omorfia menu in one place &mdash; hair, nails, massage, facials and waxing, lashes and brows, spray tanning and makeup. Prices are starting points; your provider confirms an exact quote before beginning. Members save on their club service and get 10% off everything else.</p>
  <p class="related-links">"""+_jump+"""</p>
  <a class="btn btn-primary" href="{book}">Book Appointment</a>
</section>
"""+_menu_sections+"""
""",
 faq=[("Why do some prices say 'starting at'?","Length, density, color history and service time change how much product and time a service takes. You'll have an exact quote before the service begins."),
      ("Do members get a discount?","Yes — each club includes its monthly service at member pricing, plus an unlimited 10% off all other salon and spa services and special product pricing. Month to month, no contract."),
      ("Can I book several services in one visit?","Yes — that's the point of a day spa. Stack hair, nails, massage and a facial into one appointment, or choose a spa package and save over à la carte."),
      ("Do you take walk-ins?","When the book allows, gladly — booking online or calling (845) 694-4952 is the only way to guarantee a time.")]))

# ------------------------------------------------------------------ build
os.makedirs(OUT,exist_ok=True)
PH_SLIDES_SCRIPT = """<script>
(function(){
  var wrap=document.querySelector('.ph-slides');if(!wrap)return;
  var imgs=[SLIDELIST];
  imgs.splice(imgs.indexOf("/images/slides/s08.webp"),1);
  for(var i=imgs.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=imgs[i];imgs[i]=imgs[j];imgs[j]=t;}
  imgs.unshift("/images/slides/s08.webp");
  var a=document.createElement('div'),b=document.createElement('div');
  a.className='hslide on';b.className='hslide';
  wrap.appendChild(a);wrap.appendChild(b);
  a.style.backgroundImage="url('"+imgs[0]+"')";
  if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var idx=0,front=a,back=b;
  setInterval(function(){
    idx=(idx+1)%imgs.length;
    var im=new Image();
    im.onload=function(){
      back.style.backgroundImage="url('"+imgs[idx]+"')";
      back.classList.add('on');front.classList.remove('on');
      var t=front;front=back;back=t;
    };
    im.src=imgs[idx];
  },5200);
})();
</script>""".replace("SLIDELIST", ",".join('"/images/slides/s%02d.webp"' % i for i in range(1,21)))

def inject_hero_slides(doc):
    import re as _re
    if '<section class="page-hero' not in doc:
        return doc
    did = []
    def _open(m):
        cls = m.group(1)
        if "ph-noslides" in cls:
            return m.group(0)
        if "has-photo" not in cls:
            cls += " has-photo ph-plain"
        did.append(1)
        return ('<section class="%s"%s>'
                '<div class="ph-slides" aria-hidden="true"></div>'
                '<div class="ph-veil" aria-hidden="true"></div>') % (cls, m.group(2))
    doc = _re.sub(r'<section class="(page-hero[^"]*)"([^>]*)>', _open, doc, count=1)
    if did:
        doc = doc.replace("</body>", PH_SLIDES_SCRIPT + "</body>")
    return doc

BLVD_JS = """<script>
(function(){
  var LOC='07df9e76-5ce7-4010-92d2-34fbc5ae7929', TEL='tel:+18456944952';
  function openWidget(opts){
    if(window.blvd&&blvd.openBookingWidget){
      var p={locationId:LOC};
      if(opts&&opts.path){p.path=opts.path;}
      if(opts&&opts.type){p.visitType=opts.type;}
      blvd.openBookingWidget({urlParams:p}); return true;
    }
    return false;
  }
  document.addEventListener('click',function(e){
    var a=e.target.closest('a[href="#book"],a[href="#gift"],[data-blvd-path]');
    if(!a)return;
    e.preventDefault();
    var href=a.getAttribute('href')||'';
    var opts={path:a.getAttribute('data-blvd-path'),type:a.getAttribute('data-blvd-type')};
    if(href==='#gift'&&!opts.path){opts={path:'/cart/menu/Gift%20Cards',type:'GIFT_CARD'};}
    if(!openWidget(opts)){window.location.href=TEL;}
  });
})();
</script>"""

def kw_h1(body, kw):
    """Make the keyword line the <h1> (styled as the eyebrow) and demote the tagline to .ph-title."""
    if not kw: return body
    m = re.search(r'<p class="eyebrow">(.*?)</p>(\s*)<h1>(.*?)</h1>', body, re.S)
    if not m: return body
    return body[:m.start()] + f'<h1 class="eyebrow">{kw}</h1>{m.group(2)}<p class="ph-title">{m.group(3)}</p>' + body[m.end():]

def render(p):
    canon=DOMAIN+"/"+(p["path"]+"/" if p["path"] else "")
    doc=HEAD.format(title=html.escape(p["title"]),desc=html.escape(p["desc"]),canon=canon,
                    ogimg=DOMAIN+OG_IMG.get(p["path"],OG_IMG[""]),schema=page_schema(p),book=BOOK_URL,tel=PHONE_TEL,phone=PHONE,
                    lat=GEO[0],lng=GEO[1])
    body=(kw_h1(p["body"], p.get("kw")).replace("{book}",BOOK_URL).replace("{gift}",GIFT_URL)
                   .replace("{tel}",PHONE_TEL).replace("{phone}",PHONE))
    body=re.sub(r'(/images/[^"\')\s]+)\.jpg', r'\1.webp', body)   # browsers get WebP; meta/schema keep JPG
    if p.get("faq") and not p.get("faq_done"): body+=faq_html(p["faq"])
    doc+=body
    doc+=FOOT.format(book=BOOK_URL,tel=PHONE_TEL,phone=PHONE,street=STREET,
                     city=CITY,state=STATE,zip=ZIP)
    doc=doc.replace("</body>", BLVD_JS+"</body>")
    d=os.path.join(OUT,p["path"]) if p["path"] else OUT
    os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w").write(inject_hero_slides(doc))

for p in PAGES:
    if p["path"]=="wedding": p["faq_done"]=False
    render(p)

urls=[DOMAIN+"/"]+[f'{DOMAIN}/{p["path"]}/' for p in PAGES if p["path"]]
with open(os.path.join(OUT,"sitemap.xml"),"w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for u in urls:
        pr="1.0" if u==DOMAIN+"/" else "0.8"
        f.write(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>{pr}</priority></url>\n")
    f.write("</urlset>\n")
open(os.path.join(OUT,"robots.txt"),"w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
json.dump({"cleanUrls":True,"trailingSlash":True,
  "redirects":[
    {"source":"/review","destination":f"https://search.google.com/local/writereview?placeid={PLACE_ID}","permanent":False},
    {"source":"/reviews/google","destination":f"https://search.google.com/local/reviews?placeid={PLACE_ID}","permanent":False},
    {"source":"/build.py","destination":"/","permanent":True},
    {"source":"/README.md","destination":"/","permanent":True}]},
  open(os.path.join(OUT,"vercel.json"),"w"),indent=2)
print("built",len(urls),"pages:",urls)
