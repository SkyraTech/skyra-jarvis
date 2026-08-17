// ══════════════════════════════════════════════════════════════════════════════
// Multi-Session Chat Engine & Markdown Streaming Render (chat_stream.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  let activeSessionId = "default_session";
  const cmdHistory = [];
  let historyIndex = -1;
  let activeStreamElement = null;

  // Initialize Markdown and Highlight configuration
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
      sanitize: false, // Let marked handle parse, we escape script tags
      smartypants: false,
      xhtml: false
    });

    // Custom marked renderer to output framed code blocks with headers and copy buttons
    const renderer = new marked.Renderer();
    renderer.code = function(code, lang) {
      const language = lang || 'plaintext';
      const uniqId = 'code_' + Math.random().toString(36).substr(2, 9);
      
      // Escape for safer rendering inside data-code
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

    // Send user message through WS
    window.WS.sendMessage({
      type: "user_message",
      message: text
    });

    // Save in input history
    cmdHistory.push(text);
    if (cmdHistory.length > 50) cmdHistory.shift();
    historyIndex = -1;

    // Render immediately in chat feed (user side)
    appendChatMessage("You", text, "user");
    input.value = "";

    // Save user message to active session log
    saveToSessionHistory("You", text, "user");
  }

  function handleAgentMessage(data) {
    // If we've been streaming tokens, clean up the cursor
    finalizeActiveStream();

    // Verify if it's a message from Jarvis that was not streamed
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
      // Create new message block for Jarvis response
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

    // Append token and render Markdown
    activeStreamElement.rawText += data.token;
    
    // Sanitize script tags before rendering markdown
    const sanitized = activeStreamElement.rawText.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    activeStreamElement.innerHTML = marked.parse(sanitized);

    const feed = document.getElementById("chat-feed");
    feed.scrollTop = feed.scrollHeight;
  }

  function finalizeActiveStream() {
    if (activeStreamElement) {
      const cursor = activeStreamElement.parentNode.querySelector(".stream-cursor");
      if (cursor) cursor.remove();

      // Save complete text to storage history
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

      const logItem = document.createElement("div");
      logItem.className = "tool-log-item animate-slide-up";
      logItem.style.margin = "8px 0";
      logItem.innerHTML = `
        <div class="tool-log-header" onclick="ChatStream.toggleToolLog('${logId}')">
          <span class="tool-log-name">⚙️ Tool: ${data.tool_name}</span>
          <span class="tool-log-badge ${badgeClass}">${statusText}</span>
        </div>
        <div class="tool-log-body" id="${logId}">
          <pre class="tool-log-output">${data.output_summary}</pre>
        </div>
      `;
      feed.appendChild(logItem);
      feed.scrollTop = feed.scrollHeight;

      // Draw energy beams connecting to the active port
      if (window.MCPGalaxy) {
        let matchedPort = null;
        if (data.tool_name.includes("github")) matchedPort = 8001;
        else if (data.tool_name.includes("google")) matchedPort = 8002;
        else if (data.tool_name.includes("browser")) matchedPort = 8004;
        else if (data.tool_name.includes("social")) matchedPort = 8005;
        else if (data.tool_name.includes("vision")) matchedPort = 8006;

        if (matchedPort) {
          window.MCPGalaxy.triggerDataBeam(matchedPort);
        }
      }
    }
  }

  function appendChatMessage(sender, text, styleClass) {
    const feed = document.getElementById("chat-feed");
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    // Sanitize script tags before rendering markdown
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

  // --- Session Management Storage Methods ---
  function saveToSessionHistory(sender, message, styleClass) {
    const history = JSON.parse(localStorage.getItem(`session_history_${activeSessionId}`) || "[]");
    history.push({ sender, message, styleClass, timestamp: Date.now() });
    localStorage.setItem(`session_history_${activeSessionId}`, JSON.stringify(history));
  }

  function loadSessionHistory() {
    const feed = document.getElementById("chat-feed");
    feed.innerHTML = ""; // Clear existing DOM
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

    container.innerHTML = "";
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

  // Export globally
  window.ChatStream = {
    init,
    sendMessage,
    createNewSession,
    toggleToolLog,
    copyCode
  };
})();
