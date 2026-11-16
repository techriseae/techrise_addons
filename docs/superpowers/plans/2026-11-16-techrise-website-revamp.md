# techriseae.com Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the approved AI-era hero and fix every mobile, SEO, spam and analytics issue from the 2026-11-16 audit on techriseae.com.

**Architecture:** All changes live in the Odoo 18 module `techrise_website` (QWeb views, SCSS, public JS widgets, one controller). Pure-Python helpers (spam guard, user-data hashing) get unit tests; page output gets `HttpCase` tests against the local DB; layout gets a headless-Chrome 390px check script. Deploy is phased to prod (157.230.90.9) by `git pull` + `-u techrise_website` + restart.

**Tech Stack:** Odoo 18 (QWeb, `publicWidget`, SCSS asset bundle), Python 3.12, PostgreSQL, headless Google Chrome via CDP (`websocket-client`), nginx.

**Spec:** `docs/superpowers/specs/2026-11-16-techrise-website-revamp-design.md`

## Global Constraints

- Branch `feat/site-revamp` in `/odoo18/techrise_addons`; one commit per task; bump `__manifest__.py` `version` patch number in each task that changes views/assets (`18.0.2.24.0`, `18.0.2.25.0`, …).
- Never regress a PageSpeed metric already ≥ 70 (Accessibility / Best Practices / SEO).
- Homepage H1 keeps the words "Odoo Partner" and "Abu Dhabi" (EN) / "شريك Odoo" and "أبوظبي" (AR).
- No fabricated claims: hero demo data is generic; homepage stats change only after owner decision (Task 12).
- Spam-flagged submits are logged (`_logger.info`), never silently dropped without a trace, and never create `crm.lead`.
- No plaintext email/phone in the browser beyond the form the user typed into; only SHA-256 hashes reach the thank-you page.
- Every animation respects `prefers-reduced-motion` and starts after `window.load`.
- Never `pkill -f 'http-port=8070'`; kill the preview by listening PID (`ss -ltnp | grep :8070`).

**Test command (used by every task):**
```bash
/odoo18/venv/bin/python /odoo18/odoo18-server/odoo-bin -c /etc/odoo18-server.conf \
  --http-port=8071 -d techrise_website --db-filter='^techrise_website$' \
  --addons-path=/odoo18/odoo18-server/addons,/odoo18/custom/odoo_18.0+e.latest/odoo/addons,/odoo18/techrise_addons \
  -u techrise_website --test-tags /techrise_website --stop-after-init --log-level=test 2>&1 | tail -40
```
**Mobile check (Tasks 4–7, 10, 11):** `python3 tools/mobile_check.py --base http://localhost:8070` (created in Task 4) against the :8070 preview (see memory `preview_instance_8070`).

## Review Focus

1. **Browser autofill fills the honeypot** — a real visitor whose browser autofills a hidden "website"/"company" field must not be flagged → honeypot named `tr_hp_x9`, `autocomplete="off"`, `tabindex="-1"`, `aria-hidden="true"`; test in Task 1.
2. **Form left open for days** — a submit with a 3-day-old timestamp must still create a lead (only too-fast is spam) → test in Task 1.
3. **Odd phone formats** — `"+971 50 123 4567"`, `"0501234567"`, `"00971501234567"`, `"050-123-4567"` normalize to `+971501234567`; `"12345"` or empty yields no phone hash (never a wrong hash) → tests in Task 3.
4. **No JS / reduced motion** — hero H1 and the first demo's question + answer are present in the server HTML, so crawlers and no-JS users see a complete hero → test in Task 4.
5. **Arabic hero on a phone** — `/ar` hero renders RTL with Arabic demos first and no horizontal overflow at 390px → Task 4 test + mobile check.

---

### Task 1: Spam guard on `/contact/submit`

**Files:**
- Create: `techrise_website/controllers/spam_guard.py`
- Modify: `techrise_website/controllers/__init__.py`, `techrise_website/controllers/main.py:76-105` (`contact_submit`)
- Create: `techrise_website/views/form_guard.xml` (template `techrise_website.tr_form_guard`); add to manifest `data`
- Modify: every `<form action="/contact/submit">` in `views/pages.xml:847` and `views/product_pages.xml:152,490,722,946,1170,1395` → `<t t-call="techrise_website.tr_form_guard"/>` as first child
- Create: `techrise_website/tests/__init__.py`, `techrise_website/tests/test_spam_guard.py`

**Interfaces:**
- Produces: `make_form_token(env, now: float | None = None) -> str` — `"<int ts>.<hmac>"` using `odoo.tools.misc.hmac(env(su=True), 'tr-contact-form', str(ts))`.
- Produces: `spam_reason(env, params: dict, now: float | None = None) -> str | None` — returns `'honeypot'`, `'bad_token'`, `'too_fast'` (< 3 s) or `None`.
- Produces: template `techrise_website.tr_form_guard` rendering `<input type="hidden" name="tr_ts" t-att-value="tr_form_token"/>` and the honeypot `<input name="tr_hp_x9" …>` inside a visually hidden wrapper; `tr_form_token` comes from a `website` context helper or `ir.qweb` value set in the template via `request.env`-free call — implement as a `website` method `_tr_form_token()` in `models/website.py` and call `website._tr_form_token()` in QWeb.

- [ ] **Step 1: Write failing tests** (`TransactionCase` for helpers, `HttpCase` for the route)
  - `test_token_roundtrip`: `spam_reason(env, {'tr_ts': make_form_token(env, now=1000)}, now=1010) is None`
  - `test_too_fast`: same token, `now=1001` → `'too_fast'`
  - `test_old_form_ok`: token at `now=0`, checked at `now=3*86400` → `None`
  - `test_tampered_token`: `'1000.deadbeef'` → `'bad_token'`; missing `tr_ts` → `'bad_token'`
  - `test_honeypot`: valid token + `{'tr_hp_x9': 'x'}` → `'honeypot'`
  - `test_route_spam_creates_no_lead` (HttpCase): fetch `/contactus`, scrape `csrf_token` and `tr_ts`, POST with `tr_hp_x9=spam` → status 200, thank-you page rendered, `crm.lead` count unchanged
  - `test_route_real_creates_lead`: POST with a token minted 10 s in the past (call `make_form_token(env, now=time.time()-10)`) → one new `crm.lead`
  - `test_honeypot_markup`: `/contactus` HTML contains `name="tr_hp_x9"`, `autocomplete="off"`, `tabindex="-1"`
- [ ] **Step 2: Run the test command** → FAIL (module `spam_guard` missing)
- [ ] **Step 3: Implement** `spam_guard.py`, `website._tr_form_token()`, the template, the `t-call` in all 7 forms, and in `contact_submit`: if `spam_reason(...)` → `_logger.info("contact spam blocked: %s from %s", reason, request.httprequest.remote_addr)` and render `contact_thankyou` without creating a lead
- [ ] **Step 4: Run the test command** → PASS
- [ ] **Step 5: Commit** `feat(techrise_website): honeypot + signed timing guard on contact form`

### Task 2: Cloudflare Turnstile (blocked until owner supplies site + secret keys)

**Files:** `__manifest__.py` (`depends` += `website_cf_turnstile`), `controllers/main.py` (`contact_submit`), `views/form_guard.xml`, `tests/test_spam_guard.py`

**Interfaces:**
- Consumes: Task 1's `contact_submit` flow and `tr_form_guard`.

- [ ] **Step 1:** Read `/odoo18/odoo18-server/addons/website_cf_turnstile` (and `google_recaptcha`) to find the verify entry point (expected `request.env['ir.http']._verify_request_recaptcha_token(action)`) and the widget markup it injects into website forms; note them in the commit message.
- [ ] **Step 2: Failing test** `test_turnstile_required_when_configured`: with `ir.config_parameter` `cf.turnstile_secret` set and the verify method patched to raise `UserError`, POST → no lead; patched to pass → lead.
- [ ] **Step 3:** Run → FAIL. **Step 4:** Add the widget to `tr_form_guard` (only when the site key param is set) and call the verify method in `contact_submit` after `spam_reason`. **Step 5:** Run → PASS. **Step 6:** Commit `feat(techrise_website): Cloudflare Turnstile on contact form`.

### Task 3: Enhanced Conversions user data

**Files:**
- Create: `techrise_website/controllers/user_data.py`, `techrise_website/tests/test_user_data.py`
- Modify: `controllers/main.py` (`contact_submit` passes `tr_ud` to `contact_thankyou`), `views/pages.xml:1399-1402` (thank-you `#wrap` gets `t-att-data-tr-ud-em`, `t-att-data-tr-ud-ph`), `static/src/js/main.js:282-293` (`TechriseEventTracker.start`)

**Interfaces:**
- Produces: `normalize_email(raw: str) -> str | None` (strip + lowercase; `None` if no `@`), `normalize_phone_ae(raw: str) -> str | None` (E.164; rules: strip spaces/dashes/parens; `00` → `+`; `05XXXXXXXX` (10 digits) → `+9715XXXXXXXX`; `5XXXXXXXX` (9 digits) → `+9715…`; `971…` → `+971…`; keep any other `+`-prefixed number of 8–15 digits; else `None`), `hashed_user_data(email: str, phone: str) -> dict` → `{'em': sha256hex|None, 'ph': sha256hex|None}`.
- JS: before firing `data-tr-event-fire` events, if `#wrap` has `data-tr-ud-em`/`-ph`, call `gtag('set','user_data',{sha256_email_address: em, sha256_phone_number: ph})` (omit missing keys).

- [ ] **Step 1: Failing tests**: the five phone inputs from Review Focus #3 (four → `+971501234567`, `"12345"` → `None`), `normalize_phone_ae("+44 20 7946 0958") == "+442079460958"`, `normalize_email("  Ali@Example.COM ") == "ali@example.com"`, `hashed_user_data("a@b.co","0501234567")['ph'] == hashlib.sha256(b"+971501234567").hexdigest()`; HttpCase: a real submit's thank-you HTML contains `data-tr-ud-em="<expected hash>"` and does **not** contain the plaintext email.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Manual check on :8070: submit the form, in DevTools `dataLayer` shows `set user_data` before `event contact_form_submit`.
- [ ] **Step 6:** Commit `feat(techrise_website): enhanced conversions user data on thank-you page`.

### Task 4: New homepage hero (merged design)

**Files:**
- Modify: `views/homepage.xml:10-44` (hero section), `views/seo.xml:135-150` (inline critical CSS for the new hero; drop the mobile poster `preload` at `:131` if the poster is no longer used), `static/src/scss/style.scss:234-640` (replace hero block), `__manifest__.py` assets
- Create: `static/src/js/tr_ai_console.js` (publicWidget `TechriseAiConsole`, selector `.tr-ai-console`)
- Delete: `static/src/js/tr_hero_bg.js`, `static/src/js/tr_decode_text.js`, `static/src/js/tr_splash_cursor.js` (remove from manifest; grep first that nothing else uses their classes)
- Modify: `i18n/ar_001.po` (all new hero strings)
- Create: `tools/mobile_check.py` (repo root), `techrise_website/tests/test_hero.py`

**Interfaces:**
- Markup contract: `<section class="tr-hero tr-hero--ai">` containing `<h1 id="tr-hero-title">` and `<div class="tr-ai-console" data-demos='[...]'>`; each demo `{q, think, head:[3], rows:[[3]x3], acts:[[label, kind]]}`. The **first** demo is server-rendered as static HTML inside the console (question + rows + actions) so no-JS users see it; JS takes over after `window.load`.
- `tools/mobile_check.py --base URL [--paths ...]` prints one JSON line per path `{path, sw, iw, h, bannerH, smallTargets, overflowEls}` and exits non-zero if any `sw > iw`. Default paths = all 34 sitemap paths (fetch `/sitemap.xml`). Viewport 390×844, mobile UA, consent pre-set in localStorage except for the `bannerH` probe on `/`.

Fixed copy (EN → AR):
- Badge: "Odoo Ready Partner · verified on odoo.com" → "شريك Odoo معتمد · موثّق على odoo.com" — link `https://www.odoo.com/partners?search=techrise`, `rel="noopener"`.
- H1: "The AI-powered Odoo Partner in Abu Dhabi" → "شريك Odoo المدعوم بالذكاء الاصطناعي في أبوظبي"
- Sub: "Ask your ERP in plain English or Arabic, and it answers, drafts and acts. Techrise implements Odoo accounting, CRM, HR and inventory for businesses across Abu Dhabi, Dubai and the UAE." → "اسأل نظامك بالعربي أو الإنجليزي، وهو يجاوب ويجهّز وينفّذ. تك رايز تطبّق Odoo للمحاسبة وإدارة العملاء والموارد البشرية والمخزون للشركات في أبوظبي ودبي وكل الإمارات."
- Primary CTA (keeps `data-tr-event="consultation_cta_click"`, href `/contactus`): "Get a Free AI + Odoo Consultation" → "احصل على استشارة مجانية: Odoo + الذكاء الاصطناعي"
- Secondary CTA `/services`: "Explore Our Services" → "استكشف خدماتنا"
- Demos: the three from the mockup (`https://claude.ai/artifact/5aqS3qfSaHEUWRkA82swF2`), EN first on `/`, AR first on `/ar` (AR set: "إيه الفواتير المتأخرة أكتر من 30 يوم؟", "اعرض لي المخزون اللي هيخلص الأسبوع ده", "جهّز ملف رواتب WPS للشهر ده") with Arabic column heads.

- [ ] **Step 1: Failing tests** (`HttpCase`): `/` H1 text contains "AI-powered", "Odoo Partner", "Abu Dhabi"; `/` HTML contains the first demo question and `class="tr-ai-console"`; `/` HTML contains no `tr-hero-confetti`; the frontend asset bundle no longer references `tr_hero_bg`/`tr_decode_text`/`tr_splash_cursor`; `/ar` H1 contains "شريك Odoo" and "أبوظبي" and the console's first question is Arabic.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement markup, critical CSS (H1 must paint from inline CSS alone), SCSS (dark single theme, radial glows + `radial-gradient` dot grid, two-column ≥ 992px, stacked below, secondary CTA hidden < 420px), `tr_ai_console.js` (typing ~38 ms/char, 4.2 s hold, `prefers-reduced-motion` → static), translations.
- [ ] **Step 4:** Run tests → PASS.
- [ ] **Step 5:** Start :8070 preview; `python3 tools/mobile_check.py --base http://localhost:8070 --paths / /ar` → `sw == iw` both; capture 1440 and 390 screenshots and compare against the mockup.
- [ ] **Step 6:** Lighthouse (or PSI if quota allows) on the preview: Performance not lower than the current prod run, A11y/BP/SEO ≥ prior values.
- [ ] **Step 7:** Commit `feat(techrise_website): AI copilot hero, remove matrix/confetti/splash scripts`.

### Task 5: Compact cookie bar (+ consent default decision)

**Files:** `views/layout.xml:167-200` (banner markup), `static/src/scss/style.scss` (`.tr-cookie-*`, WhatsApp FAB), `static/src/js/main.js:180-270` (banner widget), `views/seo.xml:157-175` (consent default — only if owner chose region defaults), `tests/test_layout.py`

**Interfaces:** banner keeps ids `tr-cookie-accept`, `tr-cookie-reject`, `tr-cookie-customize`, `tr-cookie-save` and storage key `tr_cookie_consent_v1` (existing consent must stay valid). When visible, `body` gets class `tr-cookie-open`, which lifts the WhatsApp FAB above the bar.

- [ ] **Step 1: Failing check:** `mobile_check.py --paths /` reports `bannerH ≤ 140` (today 510) → FAIL.
- [ ] **Step 2:** Implement: single row text (≤ 2 lines at 390px) + three buttons in one row, preferences panel opens as a sheet only on "Customize"; FAB `bottom` offset = bar height when `tr-cookie-open`; Arabic text inside the banner on `/ar/*` pages (today the body text is English).
- [ ] **Step 3:** If the owner chose "denied only for EEA/UK": add a second `gtag('consent','default',{…granted…})` and a regional `gtag('consent','default',{…denied…, region:[EEA+UK ISO codes]})`. HttpCase test asserts the `region` array is present. Otherwise skip this step and note it in the commit.
- [ ] **Step 4:** Re-run the check → `bannerH ≤ 140`, FAB rect does not intersect the Accept button rect (add this probe to `mobile_check.py`). Run the test command → PASS.
- [ ] **Step 5:** Commit `fix(techrise_website): compact mobile cookie bar, FAB no longer covers Accept`.

### Task 6: Mobile layout fixes (overflow, tap targets, homepage length)

**Files:** `views/suite_page.xml` (`/erp-suite` hero), `views/layout.xml` (footer + mobile nav links), `views/homepage.xml` (services / why-choose / how-we-work / industries sections), `static/src/scss/style.scss`

**Interfaces:** consumes `tools/mobile_check.py` (Task 4).

- [ ] **Step 1: Failing check:** `mobile_check.py` over all 34 paths: today `/ar/erp-suite` has `sw=421`; homepage `h=14941`.
- [ ] **Step 2:** Fix the RTL overflow in the suite hero (find the element with `overflowEls`; expected a fixed-width/negative-margin visual column).
- [ ] **Step 3:** Footer and mobile-menu links ≥ 40px tall touch areas (`padding-block`), social icons ≥ 40×40.
- [ ] **Step 4:** Below 768px: services and industries become 2-column compact cards (icon + title, description hidden), "Why Choose" and "How We Work" merge into one 4-item list. Target homepage `h ≤ 9000` at 390px.
- [ ] **Step 5:** Re-run → all 34 paths `sw == iw`, `/` `h ≤ 9000`, `smallTargets == 0` for nav/footer/buttons. Test command → PASS.
- [ ] **Step 6:** Commit `fix(techrise_website): mobile overflow, touch targets, shorter homepage`.

### Task 7: Complete Arabic translation

**Files:** `i18n/ar_001.po`, views where strings are not translatable (`views/suite_page.xml` `/erp-suite` content, `views/industry_pages.xml` retail/construction/healthcare `additional_title` / `website_meta_description`, product page H1 spans in `views/product_pages.xml`), `tests/test_arabic.py`

**Interfaces:** Produces helper in tests: `arabic_ratio(html: str) -> float` = Arabic letters / (Arabic + Latin letters) inside `<main>`, ignoring `<script>/<style>`, brand words "Odoo", "Techrise", "WPS", "VAT", "ERP", "CRM", "POS", "API".

- [ ] **Step 1: Failing test** `test_every_ar_page_is_arabic`: for every `/ar/*` path from `/sitemap.xml`, `arabic_ratio ≥ 0.7`, `<h1>` contains an Arabic letter, `<title>` and `meta[name=description]` contain an Arabic letter. Today fails on `/ar/erp-suite` (0%), `/ar/erp-for-retail-uae` (16%), all product-page H1s.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Translate (H1 multi-span titles need each span translatable; `additional_title` / meta via `t-if="request.lang.code.startswith('ar')"` or translated `t-set` text — pick one pattern and use it everywhere). **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(techrise_website): full Arabic translation of all /ar pages`.

### Task 8: Titles and meta descriptions

**Files:** `views/seo.xml:9-11`, `views/industry_pages.xml:13-14,158-159,297-298`, `views/suite_page.xml:12-13`, `views/product_pages.xml` (`additional_title`/`website_meta_description` per page), `views/pages.xml` (about/services/server/contact/privacy/terms), `i18n/ar_001.po`, `tests/test_seo_meta.py`

- [ ] **Step 1: Failing test** `test_titles_and_descriptions`: for all 34 sitemap paths, full `<title>` length ≤ 60, `meta[name=description]` length 120–155, no two pages share a title or description. Today 24 titles > 65 chars.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Rewrite titles as `<primary keyword> | Techrise` (e.g. "Retail ERP Software UAE — Odoo POS | Techrise"); descriptions lead with the keyword and end with a call to action; AR versions in Arabic. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `fix(techrise_website): titles ≤60 and descriptions 120–155 on every page`.

### Task 9: Structured data

**Files:** `views/seo.xml` (shared JSON-LD), product/industry/suite templates (per-page JSON-LD block via a `t-call` to a new `techrise_website.tr_jsonld_service` template taking `service_name`, `service_desc`, `faq_items`), `tests/test_schema.py`

**Interfaces:** Produces template `techrise_website.tr_jsonld_service` (params: `service_name: str`, `service_desc: str`, `faq_items: list[tuple[str,str]] | None`), emitting `Service` (provider `#organization`, areaServed AE) + `BreadcrumbList` + `FAQPage` when `faq_items`. Non-service pages get `BreadcrumbList` only via `techrise_website.tr_jsonld_breadcrumb`.

- [ ] **Step 1: Failing test** `test_jsonld`: every JSON-LD block parses with `json.loads`; each product/industry path has `Service` and `BreadcrumbList`; `/erp-for-retail-uae` and `/accounting-software-uae` have `FAQPage` whose questions exactly match visible FAQ text on the page; every non-home page has `BreadcrumbList`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; also fix `WebSite.potentialAction` target only if `/website/search` returns 200, else remove `SearchAction`. **Step 4:** Run → PASS; validate one page in Google Rich Results Test manually.
- [ ] **Step 5:** Commit `feat(techrise_website): Service, FAQPage and Breadcrumb structured data`.

### Task 10: Internal links + sitemap lastmod

**Files:** `views/layout.xml` (footer "Solutions" column), product/industry templates ("Related solutions" strip of 3 links each), `models/website.py:112` (`_enumerate_pages`), `tests/test_links_sitemap.py`

- [ ] **Step 1: Failing tests:** `test_footer_links_all_solutions`: `/` footer contains hrefs to all 6 product pages, 3 industry pages, `/erp-suite`, `/server`; `test_each_solution_has_inlinks`: every product/industry path is linked from ≥ 3 other sitemap pages' `<main>`; `test_sitemap_lastmod`: every `<url>` in `/sitemap.xml` has `<lastmod>` in `YYYY-MM-DD`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; `lastmod` = `write_date` of the page's main QWeb view (`ir.ui.view` by key) — yield it in `_enumerate_pages`. **Step 4:** Run → PASS. Mobile check stays green.
- [ ] **Step 5:** Commit `feat(techrise_website): solution links in footer and pages, sitemap lastmod`.

### Task 11: Retail ERP page depth

**Files:** `views/industry_pages.xml:290-429` (retail template), `i18n/ar_001.po`, `tests/test_retail_page.py`

**Interfaces:** consumes `tr_jsonld_service` with 6 `faq_items` (Task 9).

- [ ] **Step 1: Failing test:** `/erp-for-retail-uae` `<main>` word count ≥ 1200; ≥ 6 `<h2>`; FAQ section with 6 questions; `/ar/erp-for-retail-uae` Arabic ratio ≥ 0.7 and ≥ 900 words.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Write factual sections: UAE VAT on POS receipts, e-invoicing 2026 readiness, multi-branch stock & transfers, Odoo POS offline mode, loyalty/gift cards, e-commerce sync, reporting; 6 FAQs (pricing model, timeline, hardware, migration from existing POS, Arabic receipts, support). No invented client names or numbers. Internal links to `/inventory-procurement-uae`, `/accounting-software-uae`, `/contactus`. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(techrise_website): in-depth Retail ERP page with FAQ`.

### Task 12: Homepage stats (blocked on owner decision)

**Files:** `views/homepage.xml:46-80`
- [ ] **Step 1:** Apply owner's choice: confirmed numbers stay; replaced numbers updated (`data-target`); or the strip is replaced by the three odoo.com references (healthcare, logistics, construction) as "Projects on odoo.com". HttpCase test asserts the chosen content.
- [ ] **Step 2:** Run → PASS. **Step 3:** Commit `content(techrise_website): homepage proof strip`.

### Task 13: Server — HTTP/2 and static caching (prod, owner approves the reload)

**Files:** none in repo; `/etc/nginx/sites-enabled/<techrise site>` on 157.230.90.9. Record the final config in `docs/superpowers/ops/2026-11-nginx-techrise.md`.

HTML pages are **not** cached at nginx: every form page embeds a per-session CSRF token, and a cached copy would break submits.

- [ ] **Step 1:** Read current config (`nginx -T`), back it up to `/root/nginx-backup-2026-11-16.conf`.
- [ ] **Step 2:** `listen 443 ssl http2;` (nginx 1.24 syntax), `gzip on` for text/css/js/svg/json, `location ~* /web/assets/ { expires 365d; add_header Cache-Control "public, immutable"; }` and `/techrise_website/static/` 30 d.
- [ ] **Step 3:** `nginx -t` → OK; owner approves; `systemctl reload nginx`.
- [ ] **Step 4:** Verify: `curl -sI --http2 https://techriseae.com/ | head -1` → `HTTP/2 200`; asset response has `cache-control: public, immutable`; TTFB median of 5 runs recorded (target < 0.8 s; if not met, check Odoo `workers` / `max_cron_threads` in the prod config and note findings — no change without owner approval).
- [ ] **Step 5:** Commit the ops note.

### Task 14: Phased deploy + verification

Deploy after Tasks 1+3 (spam + conversions), after 4–6 (hero + mobile), after 7–12 (SEO/content).

- [ ] **Step 1:** Push branch state to `main` (merge) and `git push origin main`.
- [ ] **Step 2:** On server: `cd /odoo18/custom/addons/techrise_addons && git pull`; stop service, `-u techrise_website --stop-after-init`, start service (owner runs or approves; see memory `server_access`).
- [ ] **Step 3:** Verify prod: `python3 tools/mobile_check.py --base https://techriseae.com` all green; one real test submit → one lead, `contact_form_submit` visible in GA4 Realtime; spam POST (honeypot filled) → no lead, log line present.
- [ ] **Step 4:** GSC: resubmit sitemap, URL-inspect `/`, `/ar`, `/erp-for-retail-uae`, `/ar/erp-suite` → Request indexing.
- [ ] **Step 5:** Owner tasks: enable Enhanced Conversions for leads in Google Ads (519-864-1984) and "User-provided data collection" in GA4 property `G-CJTPLY088E`; mark `contact_form_submit` as key event.
