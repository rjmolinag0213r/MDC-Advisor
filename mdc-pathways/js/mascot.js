/* Finn the shark: the advisor's mascot, plus thinking orbs for each AI phase.

   Mascot states follow wobnimo's idea (github.com/Pouryaak/wobnimo): one character, a few
   moods driven by what the agent is doing: idle, listening, thinking, speaking, celebrating, sad.
   The art is our pixel shark, animated with CSS (see .shark in student-hub.html).

   Orbs come from thinking-orbs (github.com/Jakubantalik/thinking-orbs, MIT), vendored as its
   React-free engine in js/vendor. One shared clock draws every orb; orbs pause when the tab is
   hidden, and reduced-motion users get one still frame.

   API (window.Mascot):
     set(state)                    mood of the header shark
     orb(el, orbState)             turn a <span data-orb> into a 20px orb (or change its state)
     busy(el, orbState, text)      put "orb + text" in a status line; returns stop()
     phases(el, [[state, text, ms], ...])  step an orb through AI phases until el leaves the page
*/
import { resolvePreset, MODE_DRAWS } from "./vendor/thinking-orbs-engine.js";

const reduce = matchMedia("(prefers-reduced-motion: reduce)");
const DPR = Math.min(2, devicePixelRatio || 1);
const live = new Set();          // { canvas, draw, size, speed, opts }
let raf = 0;

function frame(now) {
  raf = 0;
  for (const o of live) {
    if (!o.canvas.isConnected) { live.delete(o); continue; }
    paint(o, reduce.matches ? 0.6 : (now / 1000) * o.speed);
  }
  if (live.size && !reduce.matches && document.visibilityState !== "hidden") raf = requestAnimationFrame(frame);
}
function paint(o, t) {
  const c = o.canvas.getContext("2d");
  c.setTransform(DPR, 0, 0, DPR, 0, 0);
  c.clearRect(0, 0, o.size, o.size);
  o.draw(c, o.size, t, true, o.opts);       // true = light dots for our dark hub
}
function kick() { if (!raf && live.size) raf = requestAnimationFrame(frame); }
document.addEventListener("visibilitychange", kick);
reduce.addEventListener("change", kick);

function orb(el, state = "breathing", size = 20) {
  let canvas = el.querySelector("canvas");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.width = canvas.height = Math.round(size * DPR);
    canvas.style.width = canvas.style.height = size + "px";
    canvas.setAttribute("aria-hidden", "true");
    el.prepend(canvas);
  }
  for (const o of live) if (o.canvas === canvas) live.delete(o);
  const { mode, speed, opts } = resolvePreset(state, size === 64 ? 64 : 20);
  const o = { canvas, draw: MODE_DRAWS[mode], size, speed, opts };
  live.add(o);
  el.dataset.orb = state;
  paint(o, (performance.now() / 1000) * speed);
  kick();
  return el;
}

function busy(el, state, text) {
  if (!el) return () => {};
  el.textContent = "";
  const span = document.createElement("span");
  span.className = "orb-inline";
  el.append(span, document.createTextNode(text));
  orb(span, state);
  return () => { if (span.isConnected) span.remove(); };
}

function phases(el, steps) {
  const span = el.querySelector(".orb-inline") || el.appendChild(Object.assign(document.createElement("span"), { className: "orb-inline" }));
  const label = el.querySelector(".phase") || el.appendChild(Object.assign(document.createElement("span"), { className: "phase" }));
  let i = 0;
  const step = () => {
    if (!el.isConnected || i >= steps.length) return;
    const [state, text, ms] = steps[i++];
    orb(span, state); label.textContent = text;
    if (ms) setTimeout(step, ms);
  };
  step();
}

const shark = document.getElementById("mascot");
let back = 0;
function set(state) {
  if (!shark) return;
  clearTimeout(back);
  shark.dataset.state = state;
  const badge = shark.querySelector(".shark-orb");
  if (badge) {
    badge.hidden = state !== "thinking";
    if (state === "thinking") orb(badge, "working");
  }
  const label = { idle: "Finn the shark, your advisor", listening: "Finn is listening", thinking: "Finn is thinking",
                  speaking: "Finn is answering", celebrating: "Finn is celebrating", sad: "Finn couldn't get an answer" }[state];
  if (label) shark.setAttribute("aria-label", label);
  // short moods fall back to idle on their own
  if (state === "speaking" || state === "celebrating" || state === "sad") back = setTimeout(() => set("idle"), state === "celebrating" ? 2200 : 1600);
}

window.Mascot = { set, orb, busy, phases };
set("idle");
document.dispatchEvent(new Event("mascot-ready"));
