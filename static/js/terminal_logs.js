// ══════════════════════════════════════════════════════════════════════════════
// JARVIS Diagnostics Logs Terminal Controller (terminal_logs.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  let activeFilter = "ALL";
  const logEntries = [];

  function init() {
    // 1. WebSocket Hook
    window.WS.on("log_stream", handleIncomingLog);

    // 2. Initial Microservice Health Ping checks
    checkPorts();
    setInterval(checkPorts, 15000);
  }

  function handleIncomingLog(data) {
    const entry = {
      timestamp: data.timestamp || new Date().toLocaleTimeString(),
      level: data.level || "INFO",
      message: data.message || ""
    };

    logEntries.push(entry);
    if (logEntries.length > 250) logEntries.shift(); // Bound memory limit

    renderLogs();
  }

  function renderLogs() {
    const feed = document.getElementById("logs-feed");
    if (!feed) return;

    feed.innerHTML = "";
    
    const filtered = logEntries.filter(entry => {
      if (activeFilter === "ALL") return true;
      if (activeFilter === "WARN") return entry.level === "WARN";
      if (activeFilter === "ERROR") return entry.level === "ERROR";
      if (activeFilter === "API") {
        return entry.level === "TOOL" || entry.message.toLowerCase().includes("api") || entry.message.toLowerCase().includes("http");
      }
      return true;
    });

    filtered.forEach(entry => {
      const row = document.createElement("div");
      row.className = `log-row ${entry.level.toLowerCase()}`;
      row.innerHTML = `
        <span class="log-time">[${entry.timestamp}]</span>
        <span class="log-badge ${entry.level.toLowerCase()}">${entry.level}</span>
        <span class="log-text">${escapeHtml(entry.message)}</span>
      `;
      feed.appendChild(row);
    });

    feed.scrollTop = feed.scrollHeight;
  }

  function setFilter(filter) {
    activeFilter = filter;
    
    // Toggle active state pill buttons
    document.querySelectorAll(".filter-pill").forEach(pill => {
      if (pill.innerText === filter) pill.classList.add("active");
      else if (pill.innerText !== "CLEAR" && pill.innerText !== "COPY") pill.classList.remove("active");
    });

    renderLogs();
  }

  function clearLogs() {
    logEntries.length = 0;
    renderLogs();
  }

  function copyLogs() {
    const text = logEntries.map(e => `[${e.timestamp}] [${e.level}] ${e.message}`).join("\n");
    navigator.clipboard.writeText(text).then(() => {
      const btn = document.querySelector("button[onclick*='copyLogs']");
      const original = btn.innerText;
      btn.innerText = "COPIED";
      setTimeout(() => { btn.innerText = original; }, 1500);
    });
  }

  async function checkPorts() {
    const ports = [8001, 8002, 8004, 8005, 8006];
    for (let port of ports) {
      const el = document.getElementById(`status-${port}`);
      if (!el) continue;

      try {
        const res = await fetch(`http://127.0.0.1:${port}/health`, { mode: 'cors' });
        if (res.ok) {
          el.innerText = "ACTIVE";
          el.className = "service-status up";
        } else {
          el.innerText = "STANDBY";
          el.className = "service-status down";
        }
      } catch (e) {
        el.innerText = "STANDBY";
        el.className = "service-status down";
      }
    }
  }

  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Export globally
  window.TerminalLogs = {
    init,
    setFilter,
    clearLogs,
    copyLogs,
    handleIncomingLog
  };
})();
