/* Explore page: live careers from /api/careers, roadmaps from /api/roadmap (Swarms + Prune/Gemini). */
(function () {
  "use strict";
  var input = document.getElementById("q");
  var form = document.getElementById("search-form");
  var chipsEl = document.getElementById("chips");
  var statusEl = document.getElementById("status");
  var resultsEl = document.getElementById("results");
  var backdrop = document.getElementById("rm-backdrop");
  var panel = document.getElementById("rm");
  var esc = NS.esc;

  // Interest chips (same labels as before) mapped to career ids from the backend catalog.
  var INTERESTS = [
    { id: "build", label: "Build things", careers: ["architect", "mechanical-engineer", "electrical-engineer"] },
    { id: "solve", label: "Solve puzzles", careers: ["cybersecurity-specialist", "data-analyst", "ai-engineer", "it-consultant"] },
    { id: "create", label: "Create with your hands", careers: ["chef", "architect", "software-developer"] },
    { id: "help", label: "Help people", careers: ["registered-nurse", "it-consultant", "cybersecurity-specialist"] },
    { id: "tech", label: "Technology", careers: ["software-developer", "ai-engineer", "network-engineer", "cybersecurity-specialist", "data-analyst", "it-consultant"] },
    { id: "business", label: "Business and money", careers: ["data-analyst", "it-consultant", "chef"] },
    { id: "arts", label: "Art and media", careers: ["architect", "software-developer", "chef"] },
    { id: "health", label: "Health and science", careers: ["registered-nurse", "electrical-engineer"] }
  ];
  var SYN = { computer: "tech software it", computers: "tech software it", coding: "software", code: "software",
    hacking: "cyber", hacker: "cyber", security: "cyber", cooking: "chef culinary", cook: "chef", food: "chef",
    buildings: "architect", houses: "architect", machines: "mechanical", cars: "mechanical", robots: "electrical",
    hospital: "nurse", doctor: "nurse", money: "data business", games: "software", wifi: "network", internet: "network" };

  var careers = [];
  var state = { q: "", interest: "" };
  var labelOf = {};
  INTERESTS.forEach(function (i) { labelOf[i.id] = i.label; });

  function norm(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }
  function words(q) {
    var out = [];
    norm(q).split(/[^a-z0-9]+/).filter(function (w) { return w.length > 1; }).forEach(function (w) {
      out.push(w); if (SYN[w]) out = out.concat(SYN[w].split(" "));
    });
    return out;
  }
  function score(c, ws) {
    var hay = norm([c.title, c.tagline, c.cluster, (c.keywords || []).join(" "), (c.careers || []).join(" ")].join(" "));
    return ws.reduce(function (n, w) { return n + (hay.indexOf(w) !== -1 ? (norm(c.title).indexOf(w) !== -1 ? 3 : 1) : 0); }, 0);
  }
  function search() {
    var ws = words(state.q);
    var pool = careers.filter(function (c) {
      if (!state.interest) return true;
      var i = INTERESTS.filter(function (x) { return x.id === state.interest; })[0];
      return i && i.careers.indexOf(c.id) !== -1;
    });
    if (!ws.length) return pool;
    return pool.map(function (c) { return { c: c, s: score(c, ws) }; })
      .filter(function (r) { return r.s > 0; })
      .sort(function (a, b) { return b.s - a.s; })
      .map(function (r) { return r.c; });
  }

  /* ---------- rendering ---------- */
  function renderChips() {
    chipsEl.innerHTML = INTERESTS.map(function (i) {
      return '<li><button type="button" class="chip glass" data-id="' + i.id + '" aria-pressed="' + (state.interest === i.id) + '">' + esc(i.label) + "</button></li>";
    }).join("");
  }
  chipsEl.addEventListener("click", function (e) {
    var b = e.target.closest(".chip"); if (!b) return;
    state.q = input.value; state.interest = state.interest === b.dataset.id ? "" : b.dataset.id; update();
  });

  function careerCard(c) {
    return '<li class="card glass">' +
      '<div class="meta"><span class="badge badge--cred">' + esc(c.program ? "MDC " + c.program : c.cluster) + "</span>" +
      (c.salary && c.salary.median ? '<span class="badge salary">' + NS.money(c.salary.median) + "/yr median</span>" : "") + "</div>" +
      "<h2>" + esc(c.title) + "</h2><p>" + esc(c.tagline) + "</p>" +
      "<strong>Starts at MDC with:</strong><p>" + esc(c.credential) + "</p>" +
      "<strong>Can lead to:</strong><ul class=\"careers\">" + (c.careers || []).slice(0, 4).map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" +
      '<button class="btn btn--primary glass" type="button" data-career="' + esc(c.id) + '">See my step-by-step plan</button>' +
      "</li>";
  }

  function renderResults(list) {
    var what = [];
    if (state.q.trim()) what.push("“" + state.q.trim() + "”");
    if (state.interest) what.push(labelOf[state.interest]);
    var html = list.map(careerCard).join("");
    if (state.q.trim()) {
      // Always offer an AI roadmap for exactly what they typed (custom careers outside the catalog).
      html += '<li class="card glass ai-card"><div class="meta"><span class="badge">AI roadmap</span></div>' +
        "<h2>" + esc(state.q.trim()) + "</h2><p>Don't see it? We'll build a custom plan starting at MDC.</p>" +
        '<button class="btn glass" type="button" data-query="' + esc(state.q.trim()) + '">Build a plan for “' + esc(state.q.trim()) + "”</button></li>";
    }
    resultsEl.innerHTML = html;
    statusEl.textContent = list.length
      ? list.length + (list.length === 1 ? " career" : " careers") + (what.length ? " for " + what.join(" + ") : " to explore") + "."
      : "No catalog careers matched" + (what.length ? " " + what.join(" + ") : "") + ". Try the AI plan below.";
  }

  resultsEl.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-career], button[data-query]"); if (!b) return;
    openRoadmap(b.dataset.career ? { careerId: b.dataset.career } : { query: b.dataset.query }, b);
  });

  /* ---------- roadmap panel ---------- */
  var lastTrigger = null;
  function closePanel() {
    backdrop.hidden = true; document.body.style.overflow = "";
    if (lastTrigger) lastTrigger.focus();
  }
  backdrop.addEventListener("click", function (e) { if (e.target === backdrop || e.target.closest(".close")) closePanel(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !backdrop.hidden) closePanel(); });

  // Agents write light markdown. Escape first, then allow only **bold**, headings and list dashes.
  function md(text) {
    return esc(text)
      .replace(/^#{1,4}\s*(.+)$/gm, "<b>$1</b>")
      .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
      .replace(/^\s*[-*]\s+/gm, "• ")
      .replace(/\n{3,}/g, "\n\n");
  }

  function stageHtml(s, n) {
    var body = "";
    if (s.items) body += '<ul class="tags">' + s.items.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>";
    if (s.credential) body += "<p><b>" + esc(s.credential) + "</b></p><p>" + esc(s.notes) + "</p>";
    if (s.courses) body += '<ul class="tags">' + s.courses.map(function (c) {
      return "<li>" + (c.status === "planned" ? "★ " : "") + esc(c.name) + "</li>"; }).join("") + "</ul>" +
      (s.courses.some(function (c) { return c.status === "planned"; }) ? "<p>★ suggested for your first semester</p>" : "");
    if (s.options) body += '<div class="opts">' + s.options.map(function (o) {
      return '<div class="opt glass"><b>' + esc(o.name) + "</b>" + esc(o.program) + "<br><small>" + esc(o.note) + "</small></div>"; }).join("") + "</div>";
    if (s.license) body += "<p><b>License:</b> " + esc(s.license) + "</p>";
    return '<li data-n="' + n + '"><h3>' + esc(s.title) + "</h3>" + body + "</li>";
  }

  function renderRoadmap(rm, personalizing) {
    var badge = NS.engineBadge(rm.engine);
    var html = '<button class="btn glass close" type="button" aria-label="Close">✕</button>' +
      '<h2 id="rm-title">' + esc(rm.title) + '</h2><p class="sub">' + esc(rm.tagline) + "</p>" +
      '<div class="meta">' +
      (rm.program ? '<span class="badge badge--cred">MDC ' + esc(rm.program.name) + " · " + esc(rm.program.code) + "</span>" : "") +
      (rm.salary && rm.salary.median ? '<a class="badge salary" href="' + esc(rm.salarySource.url) + '" target="_blank" rel="noopener">' + NS.money(rm.salary.median) + "/yr median · BLS</a>" : "") +
      (personalizing ? '<span class="engine loading">AI agents personalizing your plan…</span>' : badge ? '<span class="engine">' + esc(badge) + "</span>" : "") +
      "</div>";
    if (!rm.reviewed) html += '<p class="notice glass"><span>ⓘ</span><span>AI-generated for a career outside our reviewed list. Double-check with an MDC advisor.</span></p>';
    if (rm.summary || (rm.personalTips && rm.personalTips.length)) {
      html += '<section class="tips glass"><h3>Your game plan</h3>' + (rm.summary ? "<p>" + esc(rm.summary) + "</p>" : "") +
        "<ul>" + (rm.personalTips || []).map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul></section>";
    }
    html += '<ol class="steps">' + rm.stages.map(function (s, i) { return stageHtml(s, i + 1); }).join("") + "</ol>";
    if (rm.agentSteps && rm.agentSteps.length) {
      html += '<details class="agents"><summary>How the AI agents built this (Swarms)</summary>' +
        rm.agentSteps.map(function (a) { return '<div class="agent glass"><b>' + esc(a.agent) + "</b> · " + esc(a.role) + "<p>" + md(a.summary) + "</p></div>"; }).join("") +
        "</details>";
    }
    html += '<div class="cta-row"><a class="btn btn--primary glass" href="student-hub.html?go=ai">Ask the AI advisor about this</a>' +
      '<a class="btn glass" href="student-hub.html?go=progress">Plan my MDC classes</a></div>' +
      '<p class="fineprint">' + esc(rm.disclaimer) + "</p>";
    panel.innerHTML = html;
  }

  function openRoadmap(req, trigger) {
    lastTrigger = trigger || null;
    backdrop.hidden = false; document.body.style.overflow = "hidden";
    panel.innerHTML = '<p class="loading">Building your roadmap…</p>';
    panel.focus();
    var profile = { interests: state.interest ? [labelOf[state.interest]] : [] };
    var instant = req.careerId
      ? NS.api("/api/roadmap", { careerId: req.careerId, personalize: false }).then(function (rm) { renderRoadmap(rm, true); })
      : Promise.resolve();
    instant.then(function () {
      return NS.api("/api/roadmap", Object.assign({ profile: profile }, req));
    }).then(function (rm) { if (!backdrop.hidden) renderRoadmap(rm, false); })
      .catch(function (err) {
        if (backdrop.hidden) return;
        var msg = err.status === 404 ? "We don't have a plan for that yet. Try a career from the list."
          : err.status === 429 ? "Lots of requests right now. Try again in a minute." : "Couldn't build the roadmap. Please try again.";
        if (!panel.querySelector(".steps")) panel.innerHTML = '<button class="btn glass close" type="button" aria-label="Close">✕</button><h2 id="rm-title">Hmm</h2><p class="sub">' + esc(msg) + "</p>";
        else panel.querySelector(".engine") && (panel.querySelector(".engine").textContent = "MDC catalog");
      });
  }

  /* ---------- state <-> URL ---------- */
  function syncUrl() {
    var p = new URLSearchParams();
    if (state.q.trim()) p.set("q", state.q.trim());
    if (state.interest) p.set("interest", state.interest);
    var qs = p.toString();
    try { history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "")); } catch (e) {}
  }
  function update() { input.value = state.q; renderChips(); renderResults(search()); syncUrl(); }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { state.q = input.value; renderResults(search()); syncUrl(); }, 150);
  });
  form.addEventListener("submit", function (e) { e.preventDefault(); state.q = input.value; update(); });

  var params = new URLSearchParams(location.search);
  state.q = params.get("q") || "";
  state.interest = labelOf[params.get("interest")] ? params.get("interest") : "";
  renderChips();
  statusEl.innerHTML = '<span class="loading">Loading careers…</span>';
  NS.api("/api/careers").then(function (d) {
    careers = d.careers || [];
    update();
    var open = params.get("career");
    if (open) openRoadmap({ careerId: open });
  }).catch(function () {
    statusEl.textContent = "Can't reach the NextStop server. Make sure the backend is running.";
  });
  if (!state.interest) input.focus();
})();
