// ══════════════════════════════════════════════════════════════════════════════
// Multi-Window & 8-Axis Resizable Drag-Resize Manager (window_manager.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  const channel = new BroadcastChannel('jarvis_spatial_bus');
  const openedWindows = {};
  const isChildWindow = window.opener !== null;

  function init() {
    // 1. Setup BroadcastChannel listener
    channel.onmessage = (event) => {
      const { type, data } = event.data;
      if (isChildWindow) {
        handleChildChannelMessage(type, data);
      } else {
        handleParentChannelMessage(type, data);
      }
    };

    if (isChildWindow) {
      document.body.classList.add('popout-window');
      const params = new URLSearchParams(window.location.search);
      const panelId = params.get('panel');
      
      document.querySelectorAll('.hud-card').forEach(card => {
        if (card.id === panelId) {
          card.style.display = 'flex';
          card.style.position = 'static';
          card.classList.add('popout-panel');
        } else {
          card.remove();
        }
      });
      channel.postMessage({ type: 'sync_request', data: { panelId } });
    } else {
      // Setup dragging and 8-axis resizing for main elements
      setupWindowControls();
      window.addEventListener('beforeunload', closeAll);

      // Forward WebSocket events to popped out child windows
      window.WS.on("open", () => forwardToChildren("ws_open", null));
      window.WS.on("close", () => forwardToChildren("ws_close", null));
      window.WS.on("agent_message", (d) => forwardToChildren("ws_agent_message", d));
      window.WS.on("stream_token", (d) => forwardToChildren("ws_stream_token", d));
      window.WS.on("telemetry", (d) => forwardToChildren("ws_telemetry", d));
      window.WS.on("log_stream", (d) => forwardToChildren("ws_log_stream", d));
      window.WS.on("state_changed", (s) => forwardToChildren("ws_state_changed", s));
    }
  }

  // --- Drag and Resize handlers (8-Axis) ---
  function setupWindowControls() {
    const cards = document.querySelectorAll('.hud-card');
    cards.forEach(card => {
      // 1. Simple drag header movement (no tilts, clean 2D)
      const header = card.querySelector('.card-header');
      let dragStartX = 0, dragStartY = 0;

      header.addEventListener('mousedown', (e) => {
        if (e.target.closest('.card-controls')) return;
        e.preventDefault();
        
        card.classList.add('focused');
        cards.forEach(c => { if (c !== card) c.classList.remove('focused'); });

        dragStartX = e.clientX - card.offsetLeft;
        dragStartY = e.clientY - card.offsetTop;

        function onMouseMove(moveEv) {
          let top = moveEv.clientY - dragStartY;
          let left = moveEv.clientX - dragStartX;

          // Clamping screen boundaries
          top = Math.max(10, Math.min(window.innerHeight - 50, top));
          left = Math.max(10, Math.min(window.innerWidth - 100, left));

          card.style.top = top + 'px';
          card.style.left = left + 'px';
        }

        function onMouseUp() {
          document.removeEventListener('mousemove', onMouseMove);
          document.removeEventListener('mouseup', onMouseUp);
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      });

      // 2. 8-Axis resizing handlers hookup
      const resizers = card.querySelectorAll('.resize-handle');
      resizers.forEach(resizer => {
        resizer.addEventListener('mousedown', (e) => {
          e.preventDefault();
          const direction = resizer.classList[1].split('-')[1]; // e, w, n, s, ne, etc
          
          let startW = card.offsetWidth;
          let startH = card.offsetHeight;
          let startX = e.clientX;
          let startY = e.clientY;
          let startT = card.offsetTop;
          let startL = card.offsetLeft;

          function onResizeMouseMove(moveEv) {
            const dx = moveEv.clientX - startX;
            const dy = moveEv.clientY - startY;

            let newW = startW;
            let newH = startH;
            let newT = startT;
            let newL = startL;

            if (direction.includes('e')) newW = startW + dx;
            if (direction.includes('w')) {
              newW = startW - dx;
              newL = startL + dx;
            }
            if (direction.includes('s')) newH = startH + dy;
            if (direction.includes('n')) {
              newH = startH - dy;
              newT = startT + dy;
            }

            // Min constraints limits
            if (newW > 280) {
              card.style.width = newW + 'px';
              card.style.left = newL + 'px';
            }
            if (newH > 150) {
              card.style.height = newH + 'px';
              card.style.top = newT + 'px';
            }
          }

          function onResizeMouseUp() {
            document.removeEventListener('mousemove', onResizeMouseMove);
            document.removeEventListener('mouseup', onResizeMouseUp);
          }

          document.addEventListener('mousemove', onResizeMouseMove);
          document.addEventListener('mouseup', onResizeMouseUp);
        });
      });
    });
  }

  // --- Parent Broadcast channel messages ---
  function handleParentChannelMessage(type, data) {
    if (type === 'sync_request') {
      channel.postMessage({
        type: 'sync_response',
        data: {
          activeSessionId: localStorage.getItem("jarvis_active_session_id")
        }
      });
    } else if (type === 'user_input') {
      window.WS.sendMessage({
        type: "user_message",
        message: data.message
      });
    }
  }

  // --- Child Broadcast channel messages ---
  function handleChildChannelMessage(type, data) {
    if (type === 'ws_agent_message') {
      window.ChatStream.handleAgentMessage(data);
    } else if (type === 'ws_stream_token') {
      window.ChatStream.handleStreamToken(data);
    } else if (type === 'ws_telemetry') {
      window.ChatStream.handleTelemetryEvent(data);
    } else if (type === 'ws_log_stream') {
      window.TerminalLogs.handleIncomingLog(data);
    } else if (type === 'ws_state_changed') {
      window.Scene3D.updateState(data);
    }
  }

  function forwardToChildren(type, data) {
    channel.postMessage({ type, data });
  }

  // --- Window Control buttons actions ---
  function toggleMinimize(panelId) {
    const el = document.getElementById(panelId);
    if (!el) return;
    el.classList.toggle('minimized');
    if (window.SoundFX) window.SoundFX.playClick();
  }

  function toggleMaximize(panelId) {
    const el = document.getElementById(panelId);
    if (!el) return;
    el.classList.toggle('maximized');
    if (window.SoundFX) window.SoundFX.playClick();
  }

  function popOut(panelId) {
    if (isChildWindow) return;
    if (window.SoundFX) window.SoundFX.playClick();

    const url = `${window.location.origin}${window.location.pathname}?panel=${panelId}`;
    const win = window.open(url, `_blank`, `width=650,height=600,menubar=no,toolbar=no,status=no`);
    
    if (win) {
      openedWindows[panelId] = win;
      const el = document.getElementById(panelId);
      if (el) el.style.display = 'none';
    }
  }

  function closeAll() {
    Object.keys(openedWindows).forEach(k => {
      if (openedWindows[k] && !openedWindows[k].closed) {
        openedWindows[k].close();
      }
    });
  }

  // Export globally
  window.WindowManager = {
    init,
    toggleMinimize,
    toggleMaximize,
    popOut,
    closeAll
  };
})();
