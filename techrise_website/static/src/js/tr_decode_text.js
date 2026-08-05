/*
 * Techrise hero headline — cinematic "mask reveal".
 *
 * Each .tr-hero-seg word-group rises up from behind a hidden line, one after
 * another — "Your Official", then "Odoo Partner" (which keeps its gold
 * shimmer), then "in Abu Dhabi". When the last group settles, a confetti
 * flourish fires ONCE (three quick bursts, no loop). The headline then stays
 * still and readable — better for a professional B2B ERP hero than a
 * perpetual animation.
 *
 * The reveal is word-group level (not per-letter) on purpose: it keeps the
 * gold gradient shimmer on "Odoo Partner" smooth and unbroken.
 *
 * Skipped entirely for reduced-motion users — the real headline is left in
 * place, no animation, no confetti.
 */
(function () {
    "use strict";

    // Reveal pacing (ms).
    var LEAD = 180;      // delay before the first group rises
    var STEP = 460;      // gap between each group starting to rise
    var RISE = 720;      // rise transition duration (matches the CSS)
    var CONF_BURSTS = 3; // one-time celebration: 3 quick bursts
    var CONF_GAP = 300;  // ms between bursts

    function reducedMotion() {
        return window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    /* ---- Confetti: additive waves, burst upward, fade near the top so no
     * leftover debris rains back down. Self-contained canvas, no library. ---- */
    function makeConfetti(title) {
        var COLORS = ["#c9a227", "#e8c766", "#ffffff", "#1b2a4a", "#f4e2a1"];
        var canvas = document.createElement("canvas");
        canvas.className = "tr-hero-confetti";
        var host = title.parentNode; // .tr-hero-content
        if (getComputedStyle(host).position === "static") {
            host.style.position = "relative";
        }
        host.appendChild(canvas);
        var ctx = canvas.getContext("2d");
        var dpr = window.devicePixelRatio || 1;
        var parts = [];
        var running = false;

        // The canvas spans from PAD_TOP above the headline down to the
        // headline's bottom edge — it never covers the AI line underneath.
        var PAD_TOP = 90;

        function resize() {
            var r = title.getBoundingClientRect();
            var hr = host.getBoundingClientRect();
            canvas.style.left = (r.left - hr.left) + "px";
            canvas.style.top = (r.top - hr.top - PAD_TOP) + "px";
            canvas.style.width = r.width + "px";
            canvas.style.height = (r.height + PAD_TOP) + "px";
            canvas.width = Math.max(1, Math.round(r.width * dpr));
            canvas.height = Math.max(1, Math.round((r.height + PAD_TOP) * dpr));
        }

        function addWave() {
            resize();
            var w = canvas.width / dpr, h = canvas.height / dpr;
            for (var i = 0; i < 46; i++) {
                parts.push({
                    // Origin at the headline (bottom of the canvas), fired upward.
                    x: w * (0.15 + 0.7 * Math.random()),
                    y: h * (0.84 + 0.12 * Math.random()),
                    vx: (Math.random() - 0.5) * 7,
                    vy: -5 - Math.random() * 8,
                    g: 0.10 + Math.random() * 0.06,
                    size: 4 + Math.random() * 4,
                    rot: Math.random() * Math.PI,
                    vr: (Math.random() - 0.5) * 0.3,
                    color: COLORS[i % COLORS.length],
                    life: 0,
                    // Short life so each piece fans out and fades near the top of
                    // its arc — it never rains back down as leftover debris.
                    maxLife: 40 + Math.floor(Math.random() * 18),
                });
            }
        }

        function draw() {
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            var alive = [];
            for (var i = 0; i < parts.length; i++) {
                var p = parts[i];
                p.vy += p.g;
                p.x += p.vx;
                p.y += p.vy;
                p.rot += p.vr;
                p.life++;
                // Drop a piece once it fades, exits the bottom, or starts
                // falling back down — guarantees no lingering debris.
                if (p.life > p.maxLife || p.y > canvas.height / dpr + 6 || p.vy > 2.4) continue;
                ctx.save();
                ctx.globalAlpha = Math.max(0, 1 - p.life / p.maxLife);
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rot);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
                ctx.restore();
                alive.push(p);
            }
            parts = alive;
            if (parts.length) {
                requestAnimationFrame(draw);
            } else {
                running = false;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }

        return function fire() {
            addWave();
            if (!running) {
                running = true;
                requestAnimationFrame(draw);
            }
        };
    }

    function init() {
        var title = document.getElementById("tr-hero-title");
        if (!title) return;

        var segEls = Array.prototype.slice.call(
            title.querySelectorAll(".tr-hero-seg"));
        if (!segEls.length) return;

        // Reduced motion: leave the real headline, no animation.
        if (reducedMotion()) return;

        // Wrap each group's contents in a .tr-seg-rise mover. The group span
        // itself becomes the clip window; the mover is what slides up. For the
        // gold group we move the .tr-text-gold class onto the mover so its
        // gradient shimmer keeps clipping to the actual text.
        segEls.forEach(function (seg) {
            var rise = document.createElement("span");
            rise.className = "tr-seg-rise";
            if (seg.classList.contains("tr-text-gold")) {
                rise.classList.add("tr-text-gold");
            }
            while (seg.firstChild) rise.appendChild(seg.firstChild);
            seg.appendChild(rise);
        });

        // Enable the masked (hidden) starting state, then trigger the rise.
        title.classList.add("tr-decoding");

        var fireConfetti = makeConfetti(title);

        segEls.forEach(function (seg, i) {
            setTimeout(function () {
                var mover = seg.querySelector(".tr-seg-rise");
                if (mover) mover.classList.add("tr-rise-in");
            }, LEAD + i * STEP);
        });

        // One-time celebration as the final group settles.
        var doneAt = LEAD + (segEls.length - 1) * STEP + RISE - 120;
        for (var b = 0; b < CONF_BURSTS; b++) {
            setTimeout(fireConfetti, doneAt + b * CONF_GAP);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
