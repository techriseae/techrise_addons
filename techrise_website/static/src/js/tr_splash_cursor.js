/*
 * Techrise splash cursor — a soft, understated trail that follows the
 * pointer in the brand/logo colours (gold + blue). Deliberately gentle:
 * low opacity, small radius, no neon hot-spots. Pointer-events are disabled
 * so it never blocks clicks. Desktop only; skipped for touch and
 * reduced-motion users.
 */
(function () {
    "use strict";

    if (window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (window.matchMedia && !window.matchMedia("(hover: hover)").matches) return;

    // Logo palette only — warm gold + Techrise blue.
    var COLORS = [
        [245, 183, 49],   // gold   #F5B731
        [26, 93, 171],    // blue   #1A5DAB
    ];

    var canvas, ctx, w, h, dpr;
    var particles = [];
    var last = { x: null, y: null };

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        w = window.innerWidth; h = window.innerHeight;
        canvas.width = w * dpr; canvas.height = h * dpr;
        canvas.style.width = w + "px"; canvas.style.height = h + "px";
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function spawn(x, y, speed) {
        // One soft dab per move (two when moving fast) — no dense stacking.
        var n = speed > 26 ? 2 : 1;
        for (var i = 0; i < n; i++) {
            var c = COLORS[(Math.random() * COLORS.length) | 0];
            particles.push({
                x: x + (Math.random() - 0.5) * 8,
                y: y + (Math.random() - 0.5) * 8,
                vx: (Math.random() - 0.5) * 0.6,
                vy: (Math.random() - 0.5) * 0.6,
                r: 10 + Math.random() * 12 + speed * 0.25,
                life: 1,
                decay: 0.03 + Math.random() * 0.02,
                c: c,
            });
        }
        if (particles.length > 90) particles.splice(0, particles.length - 90);
    }

    function onMove(e) {
        var x = e.clientX, y = e.clientY, speed = 0;
        if (last.x !== null) speed = Math.hypot(x - last.x, y - last.y);
        last.x = x; last.y = y;
        spawn(x, y, Math.min(speed, 50));
    }

    function frame() {
        ctx.clearRect(0, 0, w, h);
        ctx.globalCompositeOperation = "lighter";
        for (var i = particles.length - 1; i >= 0; i--) {
            var p = particles[i];
            p.x += p.vx; p.y += p.vy;
            p.vx *= 0.95; p.vy *= 0.95;
            p.life -= p.decay;
            if (p.life <= 0) { particles.splice(i, 1); continue; }
            // Low peak alpha → soft glow, never a blown-out white core.
            var a = p.life * 0.16;
            var rad = p.r * (0.7 + 0.3 * p.life);
            var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, rad);
            g.addColorStop(0, "rgba(" + p.c[0] + "," + p.c[1] + "," + p.c[2] + "," + a + ")");
            g.addColorStop(1, "rgba(" + p.c[0] + "," + p.c[1] + "," + p.c[2] + ",0)");
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(p.x, p.y, rad, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalCompositeOperation = "source-over";
        requestAnimationFrame(frame);
    }

    function init() {
        canvas = document.createElement("canvas");
        canvas.className = "tr-splash-cursor";
        canvas.setAttribute("aria-hidden", "true");
        document.body.appendChild(canvas);
        ctx = canvas.getContext("2d");
        resize();
        window.addEventListener("resize", resize);
        window.addEventListener("mousemove", onMove, { passive: true });
        requestAnimationFrame(frame);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
