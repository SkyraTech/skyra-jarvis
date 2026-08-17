// ══════════════════════════════════════════════════════════════════════════════
// Resilient WebSocket Client with Heartbeat & Queue (websocket.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  let socket = null;
  let reconnectInterval = 1000;
  const maxReconnectInterval = 30000;
  const messageQueue = [];
  const eventListeners = {};
  let pingTimer = null;
  let pongTimeout = null;

  function connect() {
    socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("📡 WebSocket connection active.");
      reconnectInterval = 1000; // Reset backoff
      window.Scene3D.updateState("idle");

      // Drain offline message queue
      while (messageQueue.length > 0) {
        const payload = messageQueue.shift();
        sendMessage(payload);
      }

      startHeartbeat();
      dispatch("open", null);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Intercept Heartbeat pong response
        if (data.type === "pong") {
          clearTimeout(pongTimeout);
          return;
        }

        // Core system state updates
        if (data.status) {
          window.Scene3D.updateState(data.status);
          dispatch("state_changed", data.status);
        }

        // General event fan-out routing
        if (data.type) {
          dispatch(data.type, data);
        }
      } catch (e) {
        console.error("WebSocket message parsing error:", e);
      }
    };

    socket.onclose = () => {
      console.warn("📡 WebSocket disconnected. Attempting reconnect...");
      window.Scene3D.updateState("offline");
      stopHeartbeat();
      dispatch("close", null);

      // Exponential backoff reconnect
      setTimeout(() => {
        reconnectInterval = Math.min(reconnectInterval * 2, maxReconnectInterval);
        connect();
      }, reconnectInterval);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      socket.close();
    };
  }

  function startHeartbeat() {
    pingTimer = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ping" }));
        
        // Expect pong back within 5 seconds or force reconnect
        pongTimeout = setTimeout(() => {
          console.warn("📡 Heartbeat timeout. Forcing reconnect...");
          socket.close();
        }, 5000);
      }
    }, 10000); // 10s ping interval
  }

  function stopHeartbeat() {
    clearInterval(pingTimer);
    clearTimeout(pongTimeout);
  }

  function sendMessage(payload) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    } else {
      console.warn("📡 WebSocket disconnected. Queueing message...");
      messageQueue.push(payload);
    }
  }

  // Register event callbacks
  function on(eventType, callback) {
    if (!eventListeners[eventType]) {
      eventListeners[eventType] = [];
    }
    eventListeners[eventType].push(callback);
  }

  function dispatch(eventType, data) {
    if (eventListeners[eventType]) {
      eventListeners[eventType].forEach(cb => {
        try { cb(data); } catch(e) { console.error(e); }
      });
    }
  }

  // Export globally
  window.WS = {
    connect,
    sendMessage,
    on,
    getConnectionState: () => socket ? socket.readyState : WebSocket.CLOSED
  };
})();
