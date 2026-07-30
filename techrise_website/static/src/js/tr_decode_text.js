/*
 * Techrise decode text — the hero <h1> resolves from a stream of random
 * glyphs into the real headline on load (the "decrypt" effect seen on
 * high-end tech sites). Operates per text node, so the gold
 * `.tr-text-gold` span keeps its colour.
 *
 * Fail-safe by design: the final text is ALWAYS restored (a timer guarantees
 * it even if requestAnimationFrame is throttled in a background tab), and the
 * effect is skipped entirely for reduced-motion users or a hidden tab — so
 * the headline is never left blank.
 */
(function () {
    "use strict";

    var GLYPHS = "!<>-_\\/[]{}—=+*^?#________";

    function collectTextNodes(root) {
        var nodes = [];
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
        var n;
        while ((n = walker.nextNode())) {
            if (n.nodeValue && n.nodeValue.trim().length) nodes.push(n);
        }
        return nodes;
    }

    function scrambleNode(node, finalText, startDelay) {
        var length = finalText.length;
        var frame = 0;
        var schedule = [];
        var maxEnd = 0;
        for (var i = 0; i < length; i++) {
            var start = startDelay + Math.floor(i * 0.7);
            var end = start + 7 + Math.floor(Math.random() * 11);
            if (end > maxEnd) maxEnd = end;
            schedule.push({ start: start, end: end, ch: finalText[i] });
        }

        function tick() {
            var out = "";
            var done = true;
            for (var i = 0; i < length; i++) {
                var s = schedule[i];
                var ch = s.ch;
                if (ch === " " || ch === "\n" || ch === "\t") { out += ch; continue; }
                if (frame >= s.end) {
                    out += ch;
                } else if (frame >= s.start) {
                    done = false;
                    out += GLYPHS[(Math.random() * GLYPHS.length) | 0];
                } else {
                    done = false;
                    out += " ";
                }
            }
            node.nodeValue = out;
            frame++;
            if (!done) requestAnimationFrame(tick);
            else node.nodeValue = finalText;
        }
        requestAnimationFrame(tick);

        // Hard guarantee: whatever happens with rAF, the real text is back
        // shortly after the animation's expected duration (~60fps).
        setTimeout(function () { node.nodeValue = finalText; }, (maxEnd + 20) * 16 + 400);
    }

    function init() {
        var title = document.getElementById("tr-hero-title");
        if (!title) return;

        var nodes = collectTextNodes(title);
        var finals = nodes.map(function (n) { return n.nodeValue; });

        // Skip the animation (leave the real headline) when motion is not
        // wanted or the tab is hidden (rAF would be throttled → blank title).
        var skip = document.hidden ||
            (window.matchMedia &&
             window.matchMedia("(prefers-reduced-motion: reduce)").matches);
        if (skip) return;

        var offset = 0;
        nodes.forEach(function (node, idx) {
            scrambleNode(node, finals[idx], offset);
            offset += Math.floor(finals[idx].length * 0.7) + 4;
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
