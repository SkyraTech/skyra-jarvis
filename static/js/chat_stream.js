// ══════════════════════════════════════════════════════════════════════════════
// Multi-Session Chat Engine & Markdown Streaming Render (chat_stream.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  let activeSessionId = "default_session";
  const cmdHistory = [];
  let historyIndex = -1;
  let activeStreamElement = null;

  function init() {
    marked.setOptions({
      renderer: new marked.Renderer(),
      highlight: function(code, lang) {
        const language = hljs.getLanguage(lang) ? lang : 'plaintext';
        return hljs.highlight(code, { language }).value;
      },
      langPrefix: 'hljs language-',
      pedantic: false,
      gfm: true,
      breaks: true,
      sanitize: false,
      smartypants: false,
      xhtml: false
    });

    const renderer = new marked.Renderer();
    renderer.code = function(code, lang) {
      const language = lang || 'plaintext';
      const uniqId = 'code_' + Math.random().toString(36).substr(2, 9);
      const escapedCode = code.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

      return `
        <div class="code-block-wrap" id="${uniqId}">
          <div class="code-block-header">
            <span class="code-lang-label">${language}</span>
            <button class="copy-btn" onclick="ChatStream.copyCode('${uniqId}')">COPY</button>
          </div>
          <pre><code class="hljs language-${language}">${hljs.highlight(code, { language: hljs.getLanguage(language) ? language : 'plaintext' }).value}</code></pre>
          <div style="display:none;" class="code-raw-content">${escapedCode}</div>
        </div>
      `;
    };
    marked.use({ renderer });

    // Load active session from storage
    activeSessionId = localStorage.getItem("jarvis_active_session_id") || "default_session";
    renderSessionsList();
    loadSessionHistory();

    // WS Event Listeners
    window.WS.on("agent_message", handleAgentMessage);
    window.WS.on("stream_token", handleStreamToken);
    window.WS.on("telemetry", handleTelemetryEvent);
    
    // Command input up/down arrows history hook
    setupInputHistory();
  }

  function setupInputHistory() {
    const input = document.getElementById("chat-input");
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowUp") {
        e.preventDefault();
        if (cmdHistory.length > 0 && historyIndex < cmdHistory.length - 1) {
          historyIndex++;
          input.value = cmdHistory[cmdHistory.length - 1 - historyIndex];
        }
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (historyIndex > 0) {
          historyIndex--;
          input.value = cmdHistory[cmdHistory.length - 1 - historyIndex];
        } else if (historyIndex === 0) {
          historyIndex = -1;
          input.value = "";
        }
      }
    });
  }

  function sendMessage() {
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;

    window.WS.sendMessage({
      type: "user_message",
      message: text
    });

    cmdHistory.push(text);
    if (cmdHistory.length > 50) cmdHistory.shift();
    historyIndex = -1;

    appendChatMessage("You", text, "user");
    input.value = "";

    saveToSessionHistory("You", text, "user");
  }

  function handleAgentMessage(data) {
    finalizeActiveStream();

    if (data.sender !== "You") {
      appendChatMessage(data.sender, data.message, "jarvis");
      saveToSessionHistory(data.sender, data.message, "jarvis");
    }
  }

  function handleStreamToken(data) {
    if (data.done) {
      finalizeActiveStream();
      return;
    }

    if (!activeStreamElement) {
      const feed = document.getElementById("chat-feed");
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      
      const entry = document.createElement("div");
      entry.className = `chat-msg jarvis animate-slide-up`;
      entry.innerHTML = `
        <div class="chat-msg-meta">
          <span class="chat-msg-sender jarvis">Jarvis</span>
          <span>${timeStr}</span>
        </div>
        <div class="chat-msg-body md-body selectable"><span class="stream-text"></span><span class="stream-cursor"></span></div>
      `;
      feed.appendChild(entry);
      feed.scrollTop = feed.scrollHeight;

      activeStreamElement = entry.querySelector(".stream-text");
      activeStreamElement.rawText = "";
    }

    activeStreamElement.rawText += data.token;
    const sanitized = activeStreamElement.rawText.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    activeStreamElement.innerHTML = marked.parse(sanitized);

    const feed = document.getElementById("chat-feed");
    feed.scrollTop = feed.scrollHeight;
  }

  function finalizeActiveStream() {
    if (activeStreamElement) {
      const cursor = activeStreamElement.parentNode.querySelector(".stream-cursor");
      if (cursor) cursor.remove();

      saveToSessionHistory("Jarvis", activeStreamElement.rawText, "jarvis");
      activeStreamElement = null;
    }
  }

  function handleTelemetryEvent(data) {
    if (data.event === "tool_completed") {
      const feed = document.getElementById("chat-feed");
      const logId = 'log_' + Math.random().toString(36).substr(2, 9);
      const isSuccess = data.success;
      const statusText = isSuccess ? "SUCCESS" : "FAILED";
      const badgeClass = isSuccess ? "success" : "fail";

      // Match git diff metadata inside diagnostic logs
      let gitDiffHtml = "";
      if (data.tool_name === "run_workspace_command" && data.output_summary.includes("diff")) {
        gitDiffHtml = renderGitDiff(data.output_summary);
      }

      const logItem = document.createElement("div");
      logItem.className = "tool-log-item animate-slide-up";
      logItem.style.margin = "8px 0";
      logItem.innerHTML = `
        <div class="tool-log-header" onclick="ChatStream.toggleToolLog('${logId}')">
          <span class="tool-log-name">⚙️ Tool: ${data.tool_name}</span>
          <span class="tool-log-badge ${badgeClass}">${statusText}</span>
        </div>
        <div class="tool-log-body" id="${logId}">
          ${gitDiffHtml}
          <pre class="tool-log-output">${escapeHtml(data.output_summary)}</pre>
        </div>
      `;
      feed.appendChild(logItem);
      feed.scrollTop = feed.scrollHeight;
    }
  }

  function renderGitDiff(diffOutput) {
    const lines = diffOutput.split("\n");
    let html = '<div class="git-diff-card">';
    let currentFile = "diff_output.txt";
    let diffLines = [];

    lines.forEach(line => {
      if (line.startsWith("diff --git")) {
        if (diffLines.length > 0) {
          html += writeDiffBlock(currentFile, diffLines);
          diffLines = [];
        }
        try {
          currentFile = line.split(" b/")[1] || "file.txt";
        } catch(e) {}
      } else if (line.startsWith("+") || line.startsWith("-") || line.startsWith("@@")) {
        diffLines.push(line);
      }
    });

    if (diffLines.length > 0) {
      html += writeDiffBlock(currentFile, diffLines);
    } else {
      html += writeDiffBlock(currentFile, lines.slice(0, 15));
    }
    
    html += '</div>';
    return html;
  }

  function writeDiffBlock(filename, lines) {
    let codeStr = "";
    lines.forEach(line => {
      let cls = "";
      if (line.startsWith("+")) cls = "addition";
      else if (line.startsWith("-")) cls = "deletion";
      codeStr += `<span class="git-diff-line ${cls}">${escapeHtml(line)}</span>`;
    });

    return `
      <div class="git-diff-header">
        <span class="git-file-path">${filename}</span>
        <span class="git-change-badge mod">MODIFIED</span>
      </div>
      <pre class="git-diff-pre"><code>${codeStr}</code></pre>
    `;
  }

  function appendChatMessage(sender, text, styleClass) {
    const feed = document.getElementById("chat-feed");
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    const sanitized = text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    const htmlText = marked.parse(sanitized);

    const entry = document.createElement("div");
    entry.className = `chat-msg ${styleClass} animate-slide-up`;
    entry.innerHTML = `
      <div class="chat-msg-meta">
        <span class="chat-msg-sender ${styleClass}">${sender}</span>
        <span>${timeStr}</span>
      </div>
      <div class="chat-msg-body md-body selectable">${htmlText}</div>
    `;
    
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
  }

  function saveToSessionHistory(sender, message, styleClass) {
    const history = JSON.parse(localStorage.getItem(`session_history_${activeSessionId}`) || "[]");
    history.push({ sender, message, styleClass, timestamp: Date.now() });
    localStorage.setItem(`session_history_${activeSessionId}`, JSON.stringify(history));
  }

  function loadSessionHistory() {
    const feed = document.getElementById("chat-feed");
    feed.innerHTML = "";
    const history = JSON.parse(localStorage.getItem(`session_history_${activeSessionId}`) || "[]");
    history.forEach(item => {
      appendChatMessage(item.sender, item.message, item.styleClass);
    });
  }

  function createNewSession() {
    const newId = 'session_' + Date.now();
    const name = prompt("Enter session name:", `Session ${new Date().toLocaleDateString()}`);
    if (!name) return;

    const sessions = JSON.parse(localStorage.getItem("jarvis_sessions_list") || "[]");
    sessions.push({ id: newId, name });
    localStorage.setItem("jarvis_sessions_list", JSON.stringify(sessions));

    activeSessionId = newId;
    localStorage.setItem("jarvis_active_session_id", newId);
    
    renderSessionsList();
    loadSessionHistory();
  }

  function switchSession(id) {
    activeSessionId = id;
    localStorage.setItem("jarvis_active_session_id", id);
    renderSessionsList();
    loadSessionHistory();
  }

  function renderSessionsList() {
    const container = document.getElementById("session-sidebar");
    if (!container) return;

    let sessions = JSON.parse(localStorage.getItem("jarvis_sessions_list") || "[]");
    if (sessions.length === 0) {
      sessions = [{ id: "default_session", name: "Core Workspace" }];
      localStorage.setItem("jarvis_sessions_list", JSON.stringify(sessions));
    }

    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px; width:100%; border-bottom:1px dashed rgba(255,140,0,0.15); padding-bottom:4px;">
        <span style="font-family:var(--font-hud); font-size:0.6rem; letter-spacing:1px; color:#6b5e4e;">CHAT WORKSPACES</span>
        <button class="filter-pill" onclick="ChatStream.createNewSession()" style="padding:1px 6px;">+ NEW</button>
      </div>
    `;
    
    sessions.forEach(s => {
      const item = document.createElement("div");
      item.className = `session-item ${s.id === activeSessionId ? 'active' : ''}`;
      item.innerText = s.name;
      item.addEventListener("click", () => switchSession(s.id));
      container.appendChild(item);
    });
  }

  function toggleToolLog(logId) {
    const body = document.getElementById(logId);
    body.classList.toggle("open");
  }

  function copyCode(wrapId) {
    const wrap = document.getElementById(wrapId);
    const text = wrap.querySelector(".code-raw-content").innerText;
    
    navigator.clipboard.writeText(text).then(() => {
      const btn = wrap.querySelector(".copy-btn");
      btn.innerText = "COPIED";
      btn.classList.add("copied");
      setTimeout(() => {
        btn.innerText = "COPY";
        btn.classList.remove("copied");
      }, 2000);
    });
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
  window.ChatStream = {
    init,
    sendMessage,
    createNewSession,
    toggleToolLog,
    copyCode,
    handleAgentMessage,
    handleStreamToken,
    handleTelemetryEvent
  };
})();
