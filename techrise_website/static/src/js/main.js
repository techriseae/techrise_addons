/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.TechriseAnimations = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start: function () {
        var self = this;
        this._super.apply(this, arguments);

        // Skip the fade-in animation gate on mobile and for users that opt
        // out of motion. Adding `tr-js-ready` to body forces every
        // `.tr-animate` descendant to recompute styles (visible → hidden →
        // animate), which Lighthouse flags as a forced reflow on slow CPUs.
        var skipAnim =
            window.innerWidth < 992 ||
            (window.matchMedia &&
             window.matchMedia('(prefers-reduced-motion: reduce)').matches);

        if (!skipAnim) {
            document.body.classList.add('tr-js-ready');
        }

        // Force dark navbar immediately
        self._forceNavbarDark();

        // Run after first paint without artificial delay so LCP isn't pushed.
        var run = function () {
            self._initCounters();
            if (!skipAnim) self._initScrollAnimations();
            self._initNavbarScroll();
            self._initSmoothScroll();
            self._forceNavbarDark();
        };
        if ('requestIdleCallback' in window) {
            requestIdleCallback(run, { timeout: 800 });
        } else {
            setTimeout(run, 0);
        }
    },

    _initCounters: function () {
        var self = this;
        var counterElements = document.querySelectorAll('.tr-counter');
        var countersAnimated = new Set();

        if ('IntersectionObserver' in window) {
            var counterObserver = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting && !countersAnimated.has(entry.target)) {
                        countersAnimated.add(entry.target);
                        self._animateCounter(entry.target);
                        counterObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.3 });

            counterElements.forEach(function (el) {
                counterObserver.observe(el);
            });
        } else {
            counterElements.forEach(function (el) {
                el.textContent = el.getAttribute('data-target');
            });
        }
    },

    _animateCounter: function (el) {
        var target = parseInt(el.getAttribute('data-target'), 10);
        var duration = 2000;
        var startTime = performance.now();

        function update(currentTime) {
            var elapsed = currentTime - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = Math.round(target * eased);
            el.textContent = current;
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = target;
            }
        }
        requestAnimationFrame(update);
    },

    _initScrollAnimations: function () {
        var animateElements = document.querySelectorAll('.tr-animate');

        if ('IntersectionObserver' in window) {
            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animated');
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });

            animateElements.forEach(function (el) {
                observer.observe(el);
            });
        } else {
            animateElements.forEach(function (el) {
                el.classList.add('animated');
            });
        }
    },

    _forceNavbarDark: function () {
        var navy = '#0D1B3E';
        var isHomepage = document.getElementById('wrapwrap') &&
                         document.getElementById('wrapwrap').classList.contains('homepage');

        // On homepage: header is transparent (floats over hero video)
        // On other pages: force navy background
        if (isHomepage) {
            return;
        }

        // Force header background
        var header = document.querySelector('header.tr-navbar, header#top');
        if (header) {
            header.style.setProperty('background-color', navy, 'important');
        }
        // Force ALL nav.navbar elements inside header
        var navbars = document.querySelectorAll('header nav.navbar, header .navbar');
        navbars.forEach(function (nav) {
            nav.style.setProperty('background-color', navy, 'important');
            nav.style.setProperty('background-image', 'none', 'important');
            nav.style.setProperty('border-color', 'transparent', 'important');
        });
        // Force nav links white
        var links = document.querySelectorAll('header .nav-link, header .navbar-nav > li > a');
        links.forEach(function (link) {
            link.style.setProperty('color', '#FFFFFF', 'important');
        });
    },

    _initNavbarScroll: function () {
        var navbar = document.querySelector('.tr-navbar');
        if (navbar) {
            function handleScroll() {
                if (window.scrollY > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            }
            window.addEventListener('scroll', handleScroll, { passive: true });
            handleScroll();
        }
    },

    _initSmoothScroll: function () {
        document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
            anchor.addEventListener('click', function (e) {
                var targetId = this.getAttribute('href');
                if (targetId === '#') return;
                var targetEl = document.querySelector(targetId);
                if (targetEl) {
                    e.preventDefault();
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    },
});

// ============================================================
// HERO VIDEO REMOVED — the hero now uses an animated canvas "code field"
// background (see tr_hero_bg.js). Nothing to inject here anymore.
// ============================================================

// ============================================================
// COOKIE CONSENT BANNER — Google Consent Mode V2
// ============================================================
publicWidget.registry.TechriseCookieBanner = publicWidget.Widget.extend({
    selector: '#tr-cookie-banner',

    CONSENT_KEY: 'tr_cookie_consent_v1',

    start: function () {
        this._super.apply(this, arguments);
        var self = this;

        var saved = this._readConsent();
        if (saved) {
            this._applyConsent(saved);
            this._hideBanner();
        } else {
            this._showBanner();
        }

        var acceptBtn = this.el.querySelector('#tr-cookie-accept');
        var rejectBtn = this.el.querySelector('#tr-cookie-reject');
        var customizeBtn = this.el.querySelector('#tr-cookie-customize');
        var saveBtn = this.el.querySelector('#tr-cookie-save');
        var prefsPanel = this.el.querySelector('#tr-cookie-preferences');

        if (acceptBtn) {
            acceptBtn.addEventListener('click', function () {
                self._setConsent({ analytics: true, ads: true });
            });
        }
        if (rejectBtn) {
            rejectBtn.addEventListener('click', function () {
                self._setConsent({ analytics: false, ads: false });
            });
        }
        if (customizeBtn && prefsPanel) {
            customizeBtn.addEventListener('click', function () {
                prefsPanel.hidden = !prefsPanel.hidden;
            });
        }
        if (saveBtn) {
            saveBtn.addEventListener('click', function () {
                var analyticsCb = self.el.querySelector('#tr-cookie-analytics');
                var adsCb = self.el.querySelector('#tr-cookie-ads');
                self._setConsent({
                    analytics: analyticsCb ? analyticsCb.checked : false,
                    ads: adsCb ? adsCb.checked : false,
                });
            });
        }
    },

    _readConsent: function () {
        try {
            var raw = localStorage.getItem(this.CONSENT_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    },

    _setConsent: function (choice) {
        try {
            localStorage.setItem(this.CONSENT_KEY, JSON.stringify({
                analytics: !!choice.analytics,
                ads: !!choice.ads,
                ts: Date.now(),
            }));
        } catch (e) { /* noop */ }
        this._applyConsent(choice);
        this._hideBanner();
    },

    _applyConsent: function (choice) {
        window.dataLayer = window.dataLayer || [];
        function gtag() { window.dataLayer.push(arguments); }
        gtag('consent', 'update', {
            'ad_storage': choice.ads ? 'granted' : 'denied',
            'ad_user_data': choice.ads ? 'granted' : 'denied',
            'ad_personalization': choice.ads ? 'granted' : 'denied',
            'analytics_storage': choice.analytics ? 'granted' : 'denied',
        });
    },

    _showBanner: function () {
        this.el.classList.add('tr-cookie-visible');
    },

    _hideBanner: function () {
        this.el.classList.remove('tr-cookie-visible');
    },
});

// ============================================================
// GA4 EVENT TRACKER
// Fires gtag('event', name) for:
//   * [data-tr-event]       → on click
//   * [data-tr-event-fire]  → once on page load
// No-op when gtag isn't loaded, so safe on admin/backend pages.
// One delegated click listener → zero perf cost.
// ============================================================
publicWidget.registry.TechriseEventTracker = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start: function () {
        this._super.apply(this, arguments);

        // Page-load events (e.g. thank-you page).
        var fireOnLoad = document.querySelectorAll('[data-tr-event-fire]');
        fireOnLoad.forEach(function (el) {
            var name = el.getAttribute('data-tr-event-fire');
            if (name && typeof window.gtag === 'function') {
                window.gtag('event', name);
            }
        });

        // Click events — delegated so dynamically added nodes work too.
        document.addEventListener('click', function (ev) {
            var target = ev.target.closest('[data-tr-event]');
            if (!target) return;
            var name = target.getAttribute('data-tr-event');
            if (name && typeof window.gtag === 'function') {
                window.gtag('event', name, {
                    link_url: target.getAttribute('href') || undefined,
                });
            }
        }, { passive: true, capture: true });
    },
});

export default publicWidget.registry.TechriseAnimations;
