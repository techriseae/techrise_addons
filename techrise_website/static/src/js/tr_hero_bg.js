/*
 * Techrise hero background — a field of scattered, floating letters &
 * symbols (the X14-style "code field"), plus a gold "comet" light-streak that
 * sweeps across. Pure 2D canvas, no external library.
 *
 * Phase 1 (unify the world): this now attaches to EVERY dark hero/header —
 * the homepage `.tr-hero` and every inner-page `.tr-page-header` — so the
 * whole site shares one atmosphere instead of only the homepage. Glyphs vary
 * in size, drift slowly downward, occasionally change, and parallax toward the
 * pointer. Desktop only; a static field for reduced-motion users; the comet is
 * pure CSS and simply isn't injected when reduced motion is on.
 */
(function () {
    "use strict";

    var GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<>{}[]#%&*+=?/_^~;:!|.".split("");
    // Every dark hero/header that should carry the code field.
    var TARGETS = ".tr-hero, .tr-page-header";

    function reducedMotion() {
        return window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }
    function rand(a, b) { return a + Math.random() * (b - a); }

    // Shared pointer, read by every hero instance for its parallax.
    var mouse = { x: 0, y: 0 };
    window.addEventListener("mousemove", function (e) {
        mouse.x = e.clientX / window.innerWidth - 0.5;
        mouse.y = e.clientY / window.innerHeight - 0.5;
    }, { passive: true });

    function attach(hero) {
        var canvas = document.createElement("canvas");
        canvas.className = "tr-hero-bg";
        canvas.setAttribute("aria-hidden", "true");
        hero.insertBefore(canvas, hero.firstChild);
        var ctx = canvas.getContext("2d");

        // Gold comet streak (pure CSS animation) — skip for reduced motion.
        if (!reducedMotion()) {
            var comet = document.createElement("span");
            comet.className = "tr-comet";
            comet.setAttribute("aria-hidden", "true");
            hero.insertBefore(comet, canvas.nextSibling);
        }

        var W, H, dpr, chars = [];
        var off = { x: 0, y: 0 };

        function makeChar(y) {
            var size = rand(12, 46);
            return {
                x: rand(0, W),
                y: y === undefined ? rand(0, H) : y,
                size: size,
                ch: GLYPHS[(Math.random() * GLYPHS.length) | 0],
                a: rand(0.05, 0.28) * (1 - (size - 12) / 60),
                vy: rand(0.08, 0.5),
                gold: Math.random() < 0.07,
                flip: Math.random() * 100 | 0,
            };
        }

        function build() {
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            W = hero.clientWidth; H = hero.clientHeight;
            if (!W || !H) return;
            canvas.width = W * dpr; canvas.height = H * dpr;
            canvas.style.width = W + "px"; canvas.style.height = H + "px";
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.textBaseline = "middle";
            ctx.textAlign = "center";
            var target = Math.min(320, Math.round((W * H) / 5500));
            chars = [];
            for (var i = 0; i < target; i++) chars.push(makeChar());
        }

        function draw() {
            ctx.clearRect(0, 0, W, H);
            for (var i = 0; i < chars.length; i++) {
                var c = chars[i];
                ctx.font = c.size + "px 'Courier New', monospace";
                ctx.fillStyle = c.gold
                    ? "rgba(245,183,49," + (c.a + 0.05) + ")"
                    : "rgba(150,170,205," + c.a + ")";
                ctx.fillText(c.ch, c.x + off.x, c.y + off.y);
            }
        }

        var tick = 0;
        function animate() {
            tick++;
            for (var i = 0; i < chars.length; i++) {
                var c = chars[i];
                c.y += c.vy;
                if (c.y - c.size > H) {
                    c.y = -c.size; c.x = rand(0, W);
                    c.ch = GLYPHS[(Math.random() * GLYPHS.length) | 0];
                }
                if (((tick + c.flip) % 90) === 0) {
                    c.ch = GLYPHS[(Math.random() * GLYPHS.length) | 0];
                }
            }
            off.x += (mouse.x * 16 - off.x) * 0.05;
            off.y += (mouse.y * 16 - off.y) * 0.05;
            draw();
            requestAnimationFrame(animate);
        }

        window.addEventListener("resize", build);
        build();
        if (reducedMotion()) { draw(); return; }
        requestAnimationFrame(animate);
    }

    function init() {
        if (window.innerWidth < 992) return; // desktop only
        var heroes = document.querySelectorAll(TARGETS);
        for (var i = 0; i < heroes.length; i++) attach(heroes[i]);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
