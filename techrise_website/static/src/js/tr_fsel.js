/*
 * Techrise feature-selector — the X14 "One Platform, Four Products" pattern.
 * A vertical tab list on the left swaps a detail panel (Challenge / What it
 * does / Impact stats) on the right. Progressive-enhancement: with no JS all
 * panels are readable (SEO-safe); JS just shows one at a time and wires the
 * tabs. Keyboard accessible (Up/Down/Home/End).
 */
(function () {
    "use strict";

    function activate(root, tabs, panels, i) {
        for (var k = 0; k < tabs.length; k++) {
            var on = k === i;
            tabs[k].classList.toggle("is-active", on);
            tabs[k].setAttribute("aria-selected", on ? "true" : "false");
            tabs[k].setAttribute("tabindex", on ? "0" : "-1");
            if (panels[k]) panels[k].classList.toggle("is-active", on);
        }
    }

    function wire(root) {
        var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-tr-fsel]"));
        var panels = Array.prototype.slice.call(root.querySelectorAll("[data-tr-fsel-panel]"));
        if (!tabs.length) return;

        tabs.forEach(function (tab, i) {
            tab.addEventListener("click", function () { activate(root, tabs, panels, i); });
            tab.addEventListener("keydown", function (e) {
                var n = null;
                if (e.key === "ArrowDown" || e.key === "ArrowRight") n = (i + 1) % tabs.length;
                else if (e.key === "ArrowUp" || e.key === "ArrowLeft") n = (i - 1 + tabs.length) % tabs.length;
                else if (e.key === "Home") n = 0;
                else if (e.key === "End") n = tabs.length - 1;
                if (n !== null) { e.preventDefault(); activate(root, tabs, panels, n); tabs[n].focus(); }
            });
        });

        activate(root, tabs, panels, 0);
    }

    function init() {
        var roots = document.querySelectorAll("[data-tr-fsel-root]");
        for (var i = 0; i < roots.length; i++) wire(roots[i]);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
