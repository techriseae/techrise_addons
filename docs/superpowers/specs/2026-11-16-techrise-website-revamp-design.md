# techriseae.com revamp — design

Date: 2026-11-16 · Module: `techrise_website` (Odoo 18, repo `/odoo18/techrise_addons`) · Prod: 157.230.90.9, DB `techrise`

## Intent

The owner wants the site to read as an "AI-era" Odoo partner and to fix everything the 2026-11-16 audit found:
mobile UX, SEO, analytics, and lead quality. Today the site loads fine on Chrome, but:

- GA4 sees only visitors who click "Accept All"; `contact_form_submit` fired 0 times in 28 days.
- Nearly all CRM leads from the contact form in the last 60 days are bot spam (no CAPTCHA/honeypot).
- Google: 59 clicks / 2.31k impressions in 3 months, avg position 44.9. Retail ERP page gets the most
  impressions (1,238) but sits at positions 37–78 with 283 words.
- Mobile: cookie banner covers ~60% of the screen and the WhatsApp FAB overlaps "Accept All";
  `/ar/erp-suite` overflows (421px on a 390px screen) and is 0% Arabic.
- Arabic versions are partly English (H1s of all product pages, `/ar/erp-suite`, `/ar/erp-for-retail-uae` 16% Arabic).

Audit report: https://claude.ai/artifact/Fkj6ySwzVWXkoYjWkuTR3r · Hero mockup: https://claude.ai/artifact/5aqS3qfSaHEUWRkA82swF2

## Goals

1. New homepage hero ("merged" design, approved 2026-11-16), EN + AR.
2. Mobile: compact cookie bar, no overflow on any sitemap page, tap targets ≥ 40px, shorter homepage.
3. SEO: full Arabic translation of every `/ar/*` page, titles ≤ 60 chars, descriptions 120–155 chars,
   Service/FAQPage/BreadcrumbList schema, internal links to every product/industry page, sitemap `lastmod`,
   deeper Retail ERP page (target ≥ 1,200 words + FAQ).
4. Lead quality: contact form rejects bots (honeypot + min-fill-time server-side; Cloudflare Turnstile when keys exist).
5. Analytics: conversion events fire for real submits; Enhanced Conversions (hashed email/phone) on the thank-you page.
6. Server: HTTP/2 in nginx, long-lived caching for static assets; measure TTFB (target < 0.8s). HTML is not cached at
   nginx because form pages carry per-session CSRF tokens.

## Non-goals

- No new pages beyond what exists (except FAQ blocks inside existing pages).
- No change to brand colors, logo, or nav structure.
- No real AI backend behind the hero demo — it is a scripted, clearly illustrative animation.

## Anti-goals (failure even if it "works")

- Any PageSpeed regression on a metric already ≥ 70 (Accessibility / Best Practices / SEO) — standing guardrail.
- Losing the "Odoo Partner in Abu Dhabi" keywords from the homepage H1.
- Fabricated claims: hero demo data must be generic; homepage stats only if the owner confirms them.
- Blocking real customers (spam filter false positives) — rejected submits must still be logged.

## Approaches considered (hero)

- **A · AI copilot console** — headline + live typed question → Odoo answer → action. Shows the product in 5 s.
- **B · Neural-net canvas** — big centered headline over animated node mesh. Strong "AI" feel, explains nothing, heavier JS.
- **C · AI agents around Odoo** — four agent cards with rotating status. Strong promise the delivery must back up.
- **Picked: merged = A's console + current H1 keywords**: "The AI-powered Odoo Partner in Abu Dhabi",
  CTA "Get a Free AI + Odoo Consultation", "Odoo Ready Partner · verified on odoo.com" badge linking to
  https://www.odoo.com/partners?search=techrise, CSS-only background (radial glows + dot grid).
  Removes `tr_hero_bg.js` (matrix canvas), the confetti canvas, `tr_decode_text.js` on the hero, and `tr_splash_cursor.js`.

## Decided

- Hero headline text is plain HTML (LCP element), animation starts after `window.load`; respects `prefers-reduced-motion`.
- Console demos: 3 EN + 3 AR scripted Q&A (invoices overdue, stock running out, WPS payroll). Arabic page shows Arabic demos first.
- Mobile hero: console stacks under the copy; secondary CTA hidden < 420px.
- Spam: honeypot field + reject submits < 3 s after render (signed timestamp) server-side; flagged submits are logged, not turned into leads.
- Enhanced Conversions: server hashes (SHA-256) normalized email + E.164 phone in `/contact/submit`, thank-you page passes
  them to `gtag('set','user_data',…)` before `contact_form_submit`. No plaintext PII in the browser.

## Open — owner decides before those tasks run

1. **Consent default**: keep "denied for everyone" (current) or "denied only for EEA/UK, granted elsewhere". Legal call.
2. **Homepage stats** (100+ projects, 100+ clients, 15 countries, 30 consultants): confirm, replace, or remove.
3. **Cloudflare Turnstile keys** (site + secret) — honeypot ships without them; Turnstile is added when keys exist.
4. **Google Ads**: enable Enhanced Conversions for leads in the Ads UI + "User-provided data collection" in GA4 (owner's accounts).

## Left to the builder

Exact SCSS structure, how translations are organized in `ar_001.po`, FAQ wording (must be factual Odoo/UAE content),
nginx config details, test layout.

## Delivery

Work on branch `feat/site-revamp`, preview on local Odoo :8070 (DB `techrise_website`), deploy to prod in phases
(git pull on server + `-u techrise_website` + restart, which the owner runs or approves). Each phase verified with
the 390px headless checks and GSC/GA4 follow-up.
