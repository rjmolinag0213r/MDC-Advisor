/* NextStop client: one place for API calls and Auth0 login, shared by every MDC Pathways page.

   Usage:   <script src="js/nextstop.js"></script>
            const careers = await NS.api("/api/careers");
            const reply   = await NS.api("/api/chat", { chatHistory: [...] });
            await NS.auth.login({ returnTo: "student-hub.html?go=progress" });

   The API lives on the same server as these pages, so no URL or CORS setup is needed.
   For a frontend hosted elsewhere, set window.NEXTSTOP_API = "https://your-api" before loading this file. */
(function () {
  "use strict";
  var BASE = (window.NEXTSTOP_API || "").replace(/\/$/, "");
  var AUTH0_SDK = "https://cdn.auth0.com/js/auth0-spa-js/2.1/auth0-spa-js.production.js";
  var configPromise = null, clientPromise = null, cachedUser = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function config() {
    if (!configPromise) {
      configPromise = fetch(BASE + "/api/config").then(function (r) { return r.json(); })
        .catch(function () { return { auth0: null, demoAuth: true, programs: [] }; });
    }
    return configPromise;
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src; s.async = true; s.onload = resolve;
      s.onerror = function () { reject(new Error("Could not load " + src)); };
      document.head.appendChild(s);
    });
  }

  /* ---------- Auth0 (falls back to a demo id when the server has no Auth0 set up) ---------- */
  function client() {
    if (!clientPromise) {
      clientPromise = config().then(function (cfg) {
        if (!cfg.auth0) return null;
        return loadScript(AUTH0_SDK).then(function () {
          return window.auth0.createAuth0Client({
            domain: cfg.auth0.domain,
            clientId: cfg.auth0.clientId,
            cacheLocation: "localstorage",
            useRefreshTokens: true,
            authorizationParams: { audience: cfg.auth0.audience, redirect_uri: location.origin + location.pathname }
          });
        }).then(function (c) {
          // Finish a login redirect (?code=...&state=...) and send the student where they were going.
          var q = new URLSearchParams(location.search);
          if (q.has("code") && q.has("state")) {
            return c.handleRedirectCallback().then(function (res) {
              var to = (res && res.appState && res.appState.returnTo) || location.pathname;
              history.replaceState(null, "", location.pathname);
              if (to && to !== location.pathname) location.replace(to);
              return c;
            }).catch(function (e) { console.warn("[auth] callback failed", e); history.replaceState(null, "", location.pathname); return c; });
          }
          return c;
        });
      }).catch(function (e) { console.warn("[auth] unavailable:", e.message); return null; });
    }
    return clientPromise;
  }

  function demoId() {
    try {
      var id = localStorage.getItem("ns-demo-user");
      if (!id) { id = "student_" + Math.random().toString(36).slice(2, 10); localStorage.setItem("ns-demo-user", id); }
      return id;
    } catch (e) { return "student_demo"; }
  }

  var auth = {
    mode: function () { return config().then(function (c) { return c.auth0 ? "auth0" : (c.demoAuth ? "demo" : "none"); }); },
    isAuthenticated: function () {
      return client().then(function (c) {
        if (c) return c.isAuthenticated();
        try { return localStorage.getItem("ns-demo-in") === "1"; } catch (e) { return false; }
      });
    },
    user: function () {
      if (cachedUser) return Promise.resolve(cachedUser);
      return client().then(function (c) {
        if (c) return c.getUser().then(function (u) { cachedUser = u || null; return cachedUser; });
        return auth.isAuthenticated().then(function (ok) { return ok ? { name: "Demo student", demo: true } : null; });
      });
    },
    /* opts: { signup: bool, returnTo: "student-hub.html?go=progress" } */
    login: function (opts) {
      opts = opts || {};
      return client().then(function (c) {
        var returnTo = opts.returnTo || location.pathname;
        if (c) {
          return c.loginWithRedirect({
            appState: { returnTo: returnTo },
            authorizationParams: Object.assign({ redirect_uri: location.origin + "/student-hub.html" },
              opts.signup ? { screen_hint: "signup" } : {})
          });
        }
        try { localStorage.setItem("ns-demo-in", "1"); } catch (e) {}
        location.href = returnTo;
      });
    },
    logout: function () {
      cachedUser = null;
      return client().then(function (c) {
        try { localStorage.removeItem("ns-demo-in"); sessionStorage.removeItem("ns-sample"); } catch (e) {}
        if (c) return c.logout({ logoutParams: { returnTo: location.origin + "/" } });
        location.href = "/";
      });
    },
    headers: function () {
      return client().then(function (c) {
        if (!c) return { "X-Demo-User": demoId() };
        return c.isAuthenticated().then(function (ok) {
          if (!ok) return {};
          return c.getTokenSilently().then(function (t) { return { Authorization: "Bearer " + t }; })
            .catch(function () { return {}; });
        });
      });
    }
  };

  /* ---------- API ---------- */
  // api(path)            -> GET
  // api(path, body)      -> POST JSON (or multipart when body is FormData)
  // api(path, body, {method: "PUT", auth: true})
  function api(path, body, opts) {
    opts = opts || {};
    var method = opts.method || (body === undefined ? "GET" : "POST");
    var isForm = typeof FormData !== "undefined" && body instanceof FormData;
    var headersP = (opts.auth || /^\/api\/me\b/.test(path)) ? auth.headers() : Promise.resolve({});
    return headersP.then(function (h) {
      if (!isForm && body !== undefined) h["Content-Type"] = "application/json";
      return fetch(BASE + path, {
        method: method, headers: h,
        body: body === undefined ? undefined : (isForm ? body : JSON.stringify(body))
      });
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) {
          var err = new Error(data.message || ("Request failed (" + res.status + ")"));
          err.status = res.status; err.data = data;
          throw err;
        }
        return data;
      });
    });
  }

  /* ---------- small UI helpers shared by pages ---------- */
  function money(n) { return n == null ? "" : "$" + Math.round(n).toLocaleString("en-US"); }

  // "Powered by" line for sponsor visibility: which engine answered, and what Prune saved.
  function engineBadge(engine) {
    if (!engine) return "";
    var parts = [];
    if (engine.name === "swarms") parts.push("Swarms · " + ((engine.detail || "").match(/\d+ agents/) || ["multi-agent"])[0]);
    else if (engine.name === "llm") {
      var d = engine.detail || "";
      parts.push(/^prune\//.test(d) ? "Gemini via Prune" : /^gemini\//.test(d) ? "Gemini" : d.split("/")[0]);
    } else if (engine.name === "gemini") parts.push("Gemini vision");
    else if (engine.name === "guard") parts.push("Safety guard");
    else if (engine.name === "catalog") parts.push("MDC catalog");
    else if (engine.name === "offline" || engine.name === "parser") parts.push("Offline engine");
    var p = engine.prune;
    if (p) {
      if (p.cacheHit) parts.push("cache hit");
      if (p.tokensSaved) parts.push(p.tokensSaved + " tokens saved");
    }
    if (engine.seconds) parts.push(Number(engine.seconds).toFixed(1) + "s");
    return parts.join(" · ");
  }

  window.NS = { api: api, auth: auth, config: config, esc: esc, money: money, engineBadge: engineBadge };
  // Start Auth0 early so a login redirect (?code=...) is handled on whichever page it lands.
  client();
})();
