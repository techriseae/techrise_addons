/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/*
 * Homepage hero "AI copilot" console.
 * The first demo is already server-rendered (no-JS / crawlers / reduced
 * motion see a complete console). After window.load this widget cycles the
 * demos from data-demos with a typing effect (~38 ms/char, 4.2 s hold).
 * prefers-reduced-motion: nothing is animated, the static demo stays.
 */
const TYPE_MS = 38;
const HOLD_MS = 4200;
const THINK_MS = 500;
const RTL_RE = /[؀-ۿ]/;

publicWidget.registry.TechriseAiConsole = publicWidget.Widget.extend({
    selector: ".tr-ai-console",

    start() {
        const res = this._super(...arguments);
        this._timers = [];
        this._k = 1; // demo 0 is the server-rendered one
        let demos = [];
        try {
            demos = JSON.parse(this.el.dataset.demos || "[]");
        } catch (e) {
            demos = [];
        }
        const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (reduce || demos.length < 2) {
            return res;
        }
        this._demos = demos;
        this._ask = this.el.querySelector(".tr-ai-ask-t");
        this._ans = this.el.querySelector(".tr-ai-ans");
        this._think = this.el.querySelector(".tr-ai-think");
        this._rows = this.el.querySelector(".tr-ai-rows");
        this._act = this.el.querySelector(".tr-ai-act");
        if (!(this._ask && this._ans && this._think && this._rows && this._act)) {
            return res;
        }
        const go = () => {
            this.el.classList.add("is-live");
            this._later(() => this._play(), HOLD_MS);
        };
        if (document.readyState === "complete") {
            go();
        } else {
            this._onLoad = go;
            window.addEventListener("load", this._onLoad, { once: true });
        }
        return res;
    },

    destroy() {
        (this._timers || []).forEach((t) => clearTimeout(t));
        if (this._onLoad) {
            window.removeEventListener("load", this._onLoad);
        }
        this._super(...arguments);
    },

    _later(fn, ms) {
        this._timers.push(setTimeout(fn, ms));
    },

    _span(text, cls) {
        const s = document.createElement("span");
        s.textContent = text;
        if (cls) {
            s.className = cls;
        }
        return s;
    },

    _render(d) {
        this._think.textContent = d.think;
        this._rows.textContent = "";
        const hd = document.createElement("div");
        hd.className = "tr-ai-hd";
        d.head.forEach((t, i) => hd.appendChild(this._span(t, i === 2 ? "tr-ai-amt" : "")));
        this._rows.appendChild(hd);
        d.rows.forEach((r) => {
            const row = document.createElement("div");
            r.forEach((t, i) => row.appendChild(this._span(t, i === 1 ? "tr-ai-late" : i === 2 ? "tr-ai-amt" : "")));
            this._rows.appendChild(row);
        });
        this._act.textContent = "";
        d.acts.forEach((a) => this._act.appendChild(this._span(a[0], "tr-ai-chip " + a[1])));
    },

    _play() {
        if (document.hidden) {
            this._later(() => this._play(), 1000);
            return;
        }
        const d = this._demos[this._k % this._demos.length];
        this._k++;
        this._ans.classList.add("is-hidden");
        this._ask.textContent = "";
        this._ask.dir = RTL_RE.test(d.q) ? "rtl" : "ltr";
        this._ask.lang = RTL_RE.test(d.q) ? "ar" : "en";
        let i = 0;
        const tick = () => {
            this._ask.textContent = d.q.slice(0, ++i);
            if (i < d.q.length) {
                this._later(tick, TYPE_MS);
            } else {
                this._later(() => {
                    this._render(d);
                    this._ans.classList.remove("is-hidden");
                    this._later(() => this._play(), HOLD_MS);
                }, THINK_MS);
            }
        };
        tick();
    },
});
