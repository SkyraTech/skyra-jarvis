// ══════════════════════════════════════════════════════════════════════════════
// JARVIS MCP Constellation & Satellite Graph (mcp_galaxy.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  let scene;
  const satellites = [];
  const activeBeams = [];

  // Active microservices endpoints configuration
  const services = [
    { port: 8001, label: "GitHub Service", radius: 75, angle: 0, speed: 0.004, color: 0x60a5fa },
    { port: 8002, label: "Google Workspace", radius: 90, angle: 1.2, speed: 0.003, color: 0x10b981 },
    { port: 8004, label: "Browser Service", radius: 105, angle: 2.4, speed: 0.0025, color: 0xa855f7 },
    { port: 8005, label: "Social Broadcast", radius: 120, angle: 3.6, speed: 0.002, color: 0xec4899 },
    { port: 8006, label: "Vision Core", radius: 135, angle: 4.8, speed: 0.0015, color: 0xf59e0b }
  ];

  function init() {
    scene = window.Scene3D.getScene();
    if (!scene) {
      setTimeout(init, 100);
      return;
    }

    buildGalaxy();
    animate();

    // Check service health status immediately and poll every 15 seconds
    pollServiceHealth();
    setInterval(pollServiceHealth, 15000);
  }

  function buildGalaxy() {
    services.forEach(srv => {
      // 1. Orbital guide path line
      const pathGeom = new THREE.RingGeometry(srv.radius - 0.1, srv.radius + 0.1, 64);
      const pathMat = new THREE.MeshBasicMaterial({
        color: srv.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.04
      });
      const pathRing = new THREE.Mesh(pathGeom, pathMat);
      pathRing.rotation.x = Math.PI / 2;
      pathRing.position.y = 15;
      scene.add(pathRing);

      // 2. Satellite node mesh (glowing sphere)
      const nodeGeom = new THREE.SphereGeometry(2.5, 16, 16);
      const nodeMat = new THREE.MeshPhongMaterial({
        color: 0x3a3a3a, // Off by default (gray)
        emissive: 0x000000,
        specular: 0xffffff,
        shininess: 40
      });
      const satellite = new THREE.Mesh(nodeGeom, nodeMat);
      satellite.position.y = 15;
      scene.add(satellite);

      // 3. Hover tooltip label box
      const srvObj = {
        mesh: satellite,
        port: srv.port,
        label: srv.label,
        radius: srv.radius,
        angle: srv.angle,
        speed: srv.speed,
        color: srv.color,
        status: "down"
      };

      satellites.push(srvObj);
    });
  }

  async function pollServiceHealth() {
    for (let srv of satellites) {
      try {
        const response = await fetch(`http://127.0.0.1:${srv.port}/health`, { mode: 'cors' });
        if (response.ok) {
          updateServiceState(srv, "up");
        } else {
          updateServiceState(srv, "down");
        }
      } catch (e) {
        updateServiceState(srv, "down");
      }
    }
  }

  function updateServiceState(srv, state) {
    srv.status = state;
    const indicator = document.getElementById(`status-${srv.port}`);
    if (indicator) {
      if (state === "up") {
        indicator.innerText = "ACTIVE";
        indicator.className = "service-status up";
      } else {
        indicator.innerText = "STANDBY";
        indicator.className = "service-status down";
      }
    }

    // Update 3D Node Mesh appearance
    if (state === "up") {
      srv.mesh.material.color.setHex(srv.color);
      srv.mesh.material.emissive.setHex(srv.color);
      srv.mesh.material.emissiveIntensity = 0.5;
    } else {
      srv.mesh.material.color.setHex(0x3a3a3a);
      srv.mesh.material.emissive.setHex(0x000000);
      srv.mesh.material.emissiveIntensity = 0;
    }
  }

  function triggerDataBeam(port) {
    const srv = satellites.find(s => s.port === port);
    if (!srv || srv.status !== "up") return;

    if (window.SoundFX) window.SoundFX.playNotification();

    // Create an animated energy data beam line connecting the quantum core (0, 15, 0) to the satellite node position
    const corePos = new THREE.Vector3(0, 15, 0);
    const nodePos = srv.mesh.position.clone();

    const points = [corePos, nodePos];
    const geom = new THREE.BufferGeometry().setFromPoints(points);

    // Dynamic flashing dash material
    const lineMat = new THREE.LineDashedMaterial({
      color: srv.color,
      dashSize: 3,
      gapSize: 2,
      linewidth: 2,
      transparent: true,
      opacity: 0.8
    });

    const line = new THREE.Line(geom, lineMat);
    line.computeLineDistances();
    scene.add(line);

    const beamObj = {
      line,
      birth: Date.now(),
      duration: 1200 // lifetime 1.2 seconds
    };

    activeBeams.push(beamObj);
  }

  function animate() {
    requestAnimationFrame(animate);

    // Orbit satellites
    satellites.forEach(srv => {
      srv.angle += srv.speed;
      srv.mesh.position.x = srv.radius * Math.cos(srv.angle);
      srv.mesh.position.z = srv.radius * Math.sin(srv.angle);
    });

    // Animate energy beams scrolling dash offset + fadeout
    const now = Date.now();
    for (let i = activeBeams.length - 1; i >= 0; i--) {
      const beam = activeBeams[i];
      const elapsed = now - beam.birth;

      if (elapsed > beam.duration) {
        scene.remove(beam.line);
        beam.line.geometry.dispose();
        beam.line.material.dispose();
        activeBeams.splice(i, 1);
      } else {
        // Scroll dash effect
        beam.line.material.dashSize = 3 + Math.sin(elapsed * 0.02) * 2;
        beam.line.material.opacity = 0.8 * (1.0 - (elapsed / beam.duration));
      }
    }
  }

  // Export globally
  window.MCPGalaxy = {
    init,
    triggerDataBeam,
    getSatellites: () => satellites
  };
})();
