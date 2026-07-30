/*
 * Techrise hero background — a field of scattered, floating letters &
 * symbols (the X14-style "code field"), replacing the old video. Pure 2D
 * canvas, no external library. Glyphs vary in size, drift slowly downward,
 * occasionally change character, and the whole field parallaxes a little
 * toward the pointer. Faint grey with occasional gold accents. Desktop
 * only; a static field for reduced-motion users.
 */
(function () {
    "use strict";

    var GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<>{}[]#%&*+=?/_^~;:!|.".split("");

    function reducedMotion() {
        return window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }
    function rand(a, b) { return a + Math.random() * (b - a); }

    function init() {
        var hero = document.querySelector(".tr-hero");
        if (!hero) return;
        if (window.innerWidth < 992) return; // desktop only

        var canvas = document.createElement("canvas");
        canvas.className = "tr-hero-bg";
        canvas.setAttribute("aria-hidden", "true");
        hero.insertBefore(canvas, hero.firstChild);
        var ctx = canvas.getContext("2d");

        var W, H, dpr, chars = [];
        var mouse = { x: 0, y: 0 }, off = { x: 0, y: 0 };

        function makeChar(y) {
            var size = rand(12, 46);
            return {
                x: rand(0, W),
                y: y === undefined ? rand(0, H) : y,
                size: size,
                ch: GLYPHS[(Math.random() * GLYPHS.length) | 0],
                // Bigger glyphs are a touch fainter so nothing shouts.
                a: rand(0.05, 0.28) * (1 - (size - 12) / 60),
                vy: rand(0.08, 0.5),            // slow downward drift
                gold: Math.random() < 0.07,
                flip: Math.random() * 100 | 0,  // phase for glyph re-rolls
            };
        }

        function build() {
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            W = hero.clientWidth; H = hero.clientHeight;
            canvas.width = W * dpr; canvas.height = H * dpr;
            canvas.style.width = W + "px"; canvas.style.height = H + "px";
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.textBaseline = "middle";
            ctx.textAlign = "center";
            // Density scales with area (≈ 1 glyph per 5500 px²).
            var target = Math.min(320, Math.round((W * H) / 5500));
            chars = [];
            for (var i = 0; i < target; i++) chars.push(makeChar());
        }

        var tick = 0;
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

        function animate() {
            tick++;
            for (var i = 0; i < chars.length; i++) {
                var c = chars[i];
                c.y += c.vy;
                if (c.y - c.size > H) {          // wrap to the top
                    c.y = -c.size; c.x = rand(0, W);
                    c.ch = GLYPHS[(Math.random() * GLYPHS.length) | 0];
                }
                // Occasional glyph re-roll (subtle flicker).
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
        window.addEventListener("mousemove", function (e) {
            mouse.x = e.clientX / window.innerWidth - 0.5;
            mouse.y = e.clientY / window.innerHeight - 0.5;
        }, { passive: true });

        build();
        if (reducedMotion()) { draw(); return; }
        requestAnimationFrame(animate);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
