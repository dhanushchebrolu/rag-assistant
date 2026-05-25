/* app.js — chat frontend logic */

(() => {
  // ── session ──────────────────────────────────────────────────────────────
  function getOrCreateSession() {
    let id = localStorage.getItem("rag_session_id");
    if (!id) {
      id = "s_" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem("rag_session_id", id);
    }
    return id;
  }

  let sessionId = getOrCreateSession();

  // ── DOM refs ─────────────────────────────────────────────────────────────
  const input      = document.getElementById("msgInput");
  const sendBtn    = document.getElementById("sendBtn");
  const messages   = document.getElementById("messages");
  const welcome    = document.getElementById("welcome");
  const newChatBtn = document.getElementById("newChatBtn");
  const menuToggle = document.getElementById("menuToggle");
  const sidebar    = document.querySelector(".sidebar");
  const sessionBadge = document.getElementById("sessionBadge");

  // ── init ──────────────────────────────────────────────────────────────────
  updateSessionBadge();
  checkHealth();

  // ── health check ──────────────────────────────────────────────────────────
  async function checkHealth() {
    const dot  = document.getElementById("statusDot");
    const text = document.getElementById("statusText");
    try {
      const r = await fetch("/health");
      if (r.ok) {
        dot.className  = "status-dot healthy";
        text.textContent = "Online";
      } else {
        throw new Error();
      }
    } catch {
      dot.className  = "status-dot unhealthy";
      text.textContent = "Offline";
    }
  }

  function updateSessionBadge() {
    sessionBadge.textContent = "session " + sessionId;
  }

  // ── new chat ──────────────────────────────────────────────────────────────
  newChatBtn.addEventListener("click", async () => {
    // clear server-side history
    try {
      await fetch("/api/session/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId }),
      });
    } catch {}

    // new local session
    sessionId = "s_" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("rag_session_id", sessionId);
    updateSessionBadge();

    // restore welcome
    messages.innerHTML = "";
    const w = document.createElement("div");
    w.id = "welcome";
    w.className = "welcome";
    w.innerHTML = welcomeHTML();
    messages.appendChild(w);
    bindSuggestions();
  });

  // ── mobile sidebar ────────────────────────────────────────────────────────
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
      sidebar.classList.remove("open");
    }
  });

  // ── textarea auto-resize & enable button ─────────────────────────────────
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = input.scrollHeight + "px";
    sendBtn.disabled = input.value.trim().length === 0;
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  // ── suggestion buttons ────────────────────────────────────────────────────
  function bindSuggestions() {
    document.querySelectorAll(".suggestion").forEach((btn) => {
      btn.addEventListener("click", () => {
        input.value = btn.dataset.q;
        input.dispatchEvent(new Event("input"));
        sendMessage();
      });
    });
  }
  bindSuggestions();

  // ── main send flow ────────────────────────────────────────────────────────
  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // hide welcome
    const w = document.getElementById("welcome");
    if (w) w.remove();

    // reset input
    input.value = "";
    input.style.height = "auto";
    sendBtn.disabled = true;

    // render user bubble
    appendBubble("user", text);

    // typing indicator
    const typing = appendTyping();

    // call API
    let result;
    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, message: text }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ error: "Unknown server error." }));
        throw new Error(err.error || `HTTP ${resp.status}`);
      }

      result = await resp.json();
    } catch (err) {
      typing.remove();
      appendError(err.message || "Something went wrong. Please try again.");
      return;
    }

    typing.remove();
    appendBubble("bot", result.reply, result.sources || []);
    scrollToBottom();
  }

  // ── DOM builders ──────────────────────────────────────────────────────────
  function appendBubble(role, text, sources) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    wrapper.appendChild(bubble);

    if (role === "bot") {
      const meta = document.createElement("div");
      meta.className = "message-meta";

      if (sources && sources.length > 0) {
        // unique titles
        const seen = new Set();
        sources.forEach(s => {
          if (seen.has(s.title)) return;
          seen.add(s.title);
          const pill = document.createElement("span");
          pill.className = "source-pill";
          pill.textContent = s.title;
          meta.appendChild(pill);
        });
      }

      wrapper.appendChild(meta);
    }

    messages.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  function appendTyping() {
    const wrap = document.createElement("div");
    wrap.className = "message bot";

    const ind = document.createElement("div");
    ind.className = "typing-indicator";
    ind.innerHTML = "<span></span><span></span><span></span>";

    wrap.appendChild(ind);
    messages.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function appendError(msg) {
    const wrap = document.createElement("div");
    wrap.className = "message bot";

    const err = document.createElement("div");
    err.className = "error-bubble";
    err.textContent = "⚠ " + msg;

    wrap.appendChild(err);
    messages.appendChild(wrap);
    scrollToBottom();
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  // ── welcome HTML template ─────────────────────────────────────────────────
  function welcomeHTML() {
    return `
      <div class="welcome-icon">◆</div>
      <h2>How can I help?</h2>
      <p>Ask me anything about our platform. I'll answer using the documentation — no guessing.</p>
      <div class="suggestion-row">
        <button class="suggestion" data-q="How do I reset my password?">How do I reset my password?</button>
        <button class="suggestion" data-q="What plans do you offer?">What plans do you offer?</button>
        <button class="suggestion" data-q="How do I enable two-factor authentication?">How do I enable two-factor authentication?</button>
        <button class="suggestion" data-q="How do I export my data?">How do I export my data?</button>
      </div>
    `;
  }

})();
