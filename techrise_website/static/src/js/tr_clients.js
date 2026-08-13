/* Client selector — clicking a chip in the row swaps the featured card
 * to that company. Data lives on each chip's data-* attributes, so the
 * markup is the single source of truth and the card server-renders with
 * the first client already selected (works with JS disabled). */
(function () {
    "use strict";

    function render(chip, featured) {
        var d = chip.dataset;
        var media = featured.querySelector(".tr-spotlight-media");
        var name = featured.querySelector(".tr-featured-name");
        var sector = featured.querySelector(".tr-featured-sector");
        var desc = featured.querySelector(".tr-featured-desc");
        var tags = featured.querySelector(".tr-featured-tags");
        var link = featured.querySelector(".tr-featured-link");

        if (media) {
            var img = media.querySelector("img") || document.createElement("img");
            img.src = d.logo || "";
            img.alt = d.name || "";
            img.loading = "lazy";
            img.decoding = "async";
            if (!img.parentNode) { media.appendChild(img); }
        }
        if (name) { name.textContent = d.name || ""; }
        if (sector) {
            sector.textContent = d.sector || "";
            sector.hidden = !d.sector;
        }
        if (desc) {
            desc.textContent = d.desc || "";
            desc.hidden = !d.desc;
        }
        if (tags) {
            tags.textContent = "";
            if (d.tags) {
                d.tags.split("|").forEach(function (t) {
                    var span = document.createElement("span");
                    span.textContent = t;
                    tags.appendChild(span);
                });
            }
            tags.hidden = !d.tags;
        }
        if (link) {
            if (d.url) { link.href = d.url; link.hidden = false; }
            else { link.hidden = true; }
        }
    }

    function init() {
        var roots = document.querySelectorAll(".tr-clientsel");
        Array.prototype.forEach.call(roots, function (root) {
            var featured = root.querySelector(".tr-featured");
            var row = root.querySelector(".tr-clientsel-row");
            var track = root.querySelector(".tr-clientsel-track");
            if (!featured || !track) { return; }

            // Duplicate the chips so the track can scroll in a seamless loop.
            // Honour reduced-motion by leaving the single static set in place.
            var reduce = window.matchMedia &&
                window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            if (!reduce) {
                var originals = Array.prototype.slice.call(track.children);
                originals.forEach(function (node) {
                    var clone = node.cloneNode(true);
                    clone.setAttribute("aria-hidden", "true");
                    clone.setAttribute("tabindex", "-1");
                    clone.classList.add("is-clone");
                    track.appendChild(clone);
                });
                if (row) { row.classList.add("is-animated"); }
            }

            var chips = track.querySelectorAll(".tr-clientsel-chip");
            Array.prototype.forEach.call(chips, function (chip) {
                chip.addEventListener("click", function () {
                    Array.prototype.forEach.call(chips, function (c) {
                        c.classList.remove("is-active");
                        c.setAttribute("aria-selected", "false");
                    });
                    chip.classList.add("is-active");
                    chip.setAttribute("aria-selected", "true");
                    render(chip, featured);
                });
            });
        });
    }

    if (document.readyState !== "loading") { init(); }
    else { document.addEventListener("DOMContentLoaded", init); }
})();
