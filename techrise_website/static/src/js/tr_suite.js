/*
 * Techrise ERP Suite hero — auto-cycling dashboard deck.
 * Assigns each stacked dashboard card a position class (pos-0 = front …
 * pos-N back) and rotates them on an interval so every screenshot advances
 * to the front in turn, then recedes to the back. CSS transitions animate
 * the movement. Pauses for reduced-motion users (stays as a static stack).
 */
(function () {
    "use strict";

    function initDeck(deck) {
        var layers = Array.prototype.slice.call(
            deck.querySelectorAll(".tr-suite-layer"));
        var n = layers.length;
        if (!n) return;

        var offset = 0;
        function apply() {
            for (var i = 0; i < n; i++) {
                var pos = (i - offset + n) % n;
                layers[i].className = "tr-suite-layer pos-" + pos;
            }
        }
        apply();

        if (window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

        var timer = null;
        function start() { if (!timer) timer = setInterval(function () {
            offset = (offset + 1) % n; apply();
        }, 2600); }
        function stop() { if (timer) { clearInterval(timer); timer = null; } }

        // Only animate while the deck is on screen (saves CPU when scrolled away).
        if ("IntersectionObserver" in window) {
            new IntersectionObserver(function (entries) {
                if (entries[0].isIntersecting) start(); else stop();
            }, { threshold: 0.15 }).observe(deck);
        } else {
            start();
        }
    }

    function init() {
        var decks = document.querySelectorAll("[data-tr-deck]");
        Array.prototype.forEach.call(decks, initDeck);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
