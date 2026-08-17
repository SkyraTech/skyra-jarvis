// ══════════════════════════════════════════════════════════════════════════════
// Multi-Window Spatial Synchronization Engine (window_manager.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  const channel = new BroadcastChannel('jarvis_spatial_bus');
  const openedWindows = {};
  const isChildWindow = window.opener !== null;

  function init() {
    // 1. Hook up BroadcastChannel event hub
    channel.onmessage = (event) => {
      const { type, data } = event.data;

      if (isChildWindow) {
        handleChildChannelMessage(type, data);
      } else {
        handleParentChannelMessage(type, data);
      }
    };

    // If this is a popped out panel window, adjust styles immediately
    if (isChildWindow) {
      document.body.classList.add('popout-window');
      const params = new URLSearchParams(window.location.search);
      const panelId = params.get('panel');
      
      // Hide all panels except the one target
      document.querySelectorAll('.hud-card').forEach(card => {
        if (card.id === panelId) {
          card.style.display = 'block';
          card.classList.add('popout-panel');
        } else {
          card.remove();
        }
      });

      // Synchronize initial state from parent
      channel.postMessage({ type: 'sync_request', data: { panelId } });
    }

    // Unload hook to clean up child windows on parent close
    if (!isChildWindow) {
      window.addEventListener('beforeunload', () => {
        closeAll();
      });
    }

    // Listen to WS events from WS client in the parent window and broadcast to children
    if (!isChildWindow) {
      window.WS.on("open", () => forwardToChildren("ws_open", null));
      window.WS.on("close", () => forwardToChildren("ws_close", null));
      window.WS.on("agent_message", (d) => forwardToChildren("ws_agent_message", d));
      window.WS.on("stream_token", (d) => forwardToChildren("ws_stream_token", d));
      window.WS.on("telemetry", (d) => forwardToChildren("ws_telemetry", d));
      window.WS.on("state_changed", (s) => forwardToChildren("ws_state_changed", s));
    }
  }

  // --- Parent Broadcast handlers ---
  function handleParentChannelMessage(type, data) {
    if (type === 'sync_request') {
      // Send active state back to the child window
      channel.postMessage({
        type: 'sync_response',
        data: {
          activeSessionId: localStorage.getItem("jarvis_active_session_id")
        }
      });
    } else if (type === 'user_input') {
      // Child window sent input -> forward to parent WS connection
      window.WS.sendMessage({
        type: "user_message",
        message: data.message
      });
    }
  }

  // --- Child Panel Sync handlers ---
  function handleChildChannelMessage(type, data) {
    if (type === 'sync_response') {
      console.log("📡 Initial sync complete from parent workspace.");
    } else if (type === 'ws_agent_message') {
      // Child panel receives WS message from parent connection
      if (window.WS && window.WS.dispatch) {
        // If WS exists locally inside child window, manually trigger the event handler
        window.WS.dispatch("agent_message", data);
      } else {
        // Trigger via globally exposed handler directly
        window.ChatStream.handleAgentMessage(data);
      }
    } else if (type === 'ws_stream_token') {
      window.ChatStream.handleStreamToken(data);
    } else if (type === 'ws_telemetry') {
      window.ChatStream.handleTelemetryEvent(data);
    } else if (type === 'ws_state_changed') {
      window.Scene3D.updateState(data);
    }
  }

  function forwardToChildren(type, data) {
    channel.postMessage({ type, data });
  }

  // --- Pop-Out Frameless Window Spawn ---
  function popOut(panelId) {
    if (isChildWindow) return;

    if (window.SoundFX) window.SoundFX.playClick();

    // Spawns independent frameless window targetting this panel specifically
    const url = `${window.location.origin}${window.location.pathname}?panel=${panelId}`;
    const win = window.open(
      url,
      `_blank`,
      `width=800,height=600,menubar=no,toolbar=no,location=no,status=no`
    );

    if (win) {
      openedWindows[panelId] = win;
      // Hide the panel inside the parent 3D space to avoid duplicates
      const card = document.getElementById(panelId);
      if (card) card.style.display = 'none';
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
    popOut,
    closeAll
  };
})();
