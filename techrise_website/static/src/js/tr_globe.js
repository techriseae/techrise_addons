/*
 * Techrise signature globe — a rotating dotted wireframe sphere (the X14-style
 * globe) drawn on a transparent 2D canvas, no external library. A Fibonacci
 * point cloud rotates around the Y axis with a fixed tilt; latitude/longitude
 * great circles are stroked with depth-based alpha so the back of the grid
 * reads dimmer. Gold on transparent, so it sits over the code-field hero.
 *
 * Usage: <canvas class="tr-globe" data-tr-globe aria-hidden="true"></canvas>
 * inside a sized square container. Reduced motion → drawn once, static.
 */
(function () {
    "use strict";

    function reducedMotion() {
        return window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function attach(canvas) {
        var ctx = canvas.getContext("2d");
        var dpr = Math.min(window.devicePixelRatio || 1, 2);
        // Colours are overridable per-canvas (rgb triplets) so one globe can be
        // gold (hero) and another blue (Our Story) from the same script.
        var dotRGB = canvas.getAttribute("data-tr-globe-dot") || "240,196,90";
        var lineRGB = canvas.getAttribute("data-tr-globe-line") || "236,182,63";
        var TILT = -0.42;                 // fixed north-up tilt
        var cs = Math.cos(TILT), sn = Math.sin(TILT);
        var angle = 0;
        var R, cx, cy;

        // Fibonacci sphere point cloud.
        var N = 620, dots = [];
        (function () {
            var ga = Math.PI * (3 - Math.sqrt(5));
            for (var i = 0; i < N; i++) {
                var y = 1 - (i / (N - 1)) * 2;
                var r = Math.sqrt(1 - y * y);
                var th = ga * i;
                dots.push([Math.cos(th) * r, y, Math.sin(th) * r]);
            }
        })();

        // Latitude + longitude great-circle rings (as vertex arrays).
        var rings = [];
        (function () {
            var seg = 90, k, t, i;
            for (k = -2; k <= 2; k++) {          // latitude circles
                var lat = k * 0.55, yy = Math.sin(lat), rr = Math.cos(lat), arr = [];
                for (i = 0; i <= seg; i++) { t = (i / seg) * Math.PI * 2; arr.push([rr * Math.cos(t), yy, rr * Math.sin(t)]); }
                rings.push(arr);
            }
            for (k = 0; k < 6; k++) {             // meridians
                var lon = (k / 6) * Math.PI, cl = Math.cos(lon), sl = Math.sin(lon), a2 = [];
                for (i = 0; i <= seg; i++) { t = (i / seg) * Math.PI * 2; a2.push([Math.cos(t) * cl, Math.sin(t), Math.cos(t) * sl]); }
                rings.push(a2);
            }
        })();

        function size() {
            var w = canvas.clientWidth, h = canvas.clientHeight;
            if (!w || !h) return;
            canvas.width = w * dpr; canvas.height = h * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            cx = w / 2; cy = h / 2;
            R = Math.min(w, h) * 0.46;
        }

        // Rotate around Y by `angle`, tilt around X by TILT, orthographic.
        function project(p) {
            var ca = Math.cos(angle), sa = Math.sin(angle);
            var x = p[0] * ca + p[2] * sa;
            var z = -p[0] * sa + p[2] * ca;
            var y = p[1];
            var yy = y * cs - z * sn;
            var zz = y * sn + z * cs;
            return [cx + x * R, cy + yy * R, zz]; // zz = depth (+ toward viewer)
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Soft outer glow rim.
            ctx.beginPath();
            ctx.arc(cx, cy, R + 2, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(" + lineRGB + ",0.28)";
            ctx.lineWidth = 1;
            ctx.stroke();

            // Wireframe rings, per-segment depth alpha.
            for (var r = 0; r < rings.length; r++) {
                var pts = rings[r], prev = project(pts[0]);
                for (var i = 1; i < pts.length; i++) {
                    var cur = project(pts[i]);
                    var d = (prev[2] + cur[2]) / 2;            // -1..1
                    var a = 0.05 + 0.20 * ((d + 1) / 2);
                    ctx.beginPath();
                    ctx.moveTo(prev[0], prev[1]);
                    ctx.lineTo(cur[0], cur[1]);
                    ctx.strokeStyle = "rgba(" + lineRGB + "," + a.toFixed(3) + ")";
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    prev = cur;
                }
            }

            // Dot cloud on top.
            for (var k = 0; k < dots.length; k++) {
                var p = project(dots[k]);
                var f = (p[2] + 1) / 2;                        // 0 back .. 1 front
                var a2 = 0.15 + 0.75 * f;
                var rad = 0.7 + 1.4 * f;
                ctx.beginPath();
                ctx.arc(p[0], p[1], rad, 0, Math.PI * 2);
                ctx.fillStyle = "rgba(" + dotRGB + "," + a2.toFixed(3) + ")";
                ctx.fill();
            }
        }

        function frame() {
            angle += 0.0024;
            draw();
            requestAnimationFrame(frame);
        }

        window.addEventListener("resize", function () { size(); });
        size();
        if (reducedMotion()) { draw(); return; }
        requestAnimationFrame(frame);
    }

    function init() {
        var nodes = document.querySelectorAll("[data-tr-globe]");
        for (var i = 0; i < nodes.length; i++) attach(nodes[i]);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
