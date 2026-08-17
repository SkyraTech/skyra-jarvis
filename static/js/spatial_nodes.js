// ══════════════════════════════════════════════════════════════════════════════
// JARVIS Spatial UI Windows Manager — CSS3D Floating Panels (spatial_nodes.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  let cssScene, cssRenderer;
  const panels = {};
  const activeFocus = null;

  // Position slots in 3D space around the center core
  const spatialSlots = {
    "panel-core":      { pos: [-90, 45, 10], rot: [0, 0.45, 0] },
    "panel-agents":    { pos: [110, 50, -20], rot: [0, -0.45, 0] },
    "panel-telemetry": { pos: [-90, -20, 40], rot: [-0.15, 0.45, 0] },
    "panel-terminal":  { pos: [0, -45, 80], rot: [-0.25, 0, 0] },
    "panel-system":    { pos: [110, -15, 20], rot: [-0.15, -0.45, 0] }
  };

  function init() {
    cssScene = new THREE.Scene();

    cssRenderer = new THREE.CSS3DRenderer();
    cssRenderer.setSize(window.innerWidth, window.innerHeight);
    cssRenderer.domElement.className = 'css3d-layer';
    document.getElementById('canvas-container').appendChild(cssRenderer.domElement);

    // Load panels from DOM elements
    const elements = document.querySelectorAll('.hud-card');
    elements.forEach(el => {
      const id = el.id;
      const slot = spatialSlots[id] || { pos: [0, 0, 0], rot: [0, 0, 0] };

      // Retain or restore saved coordinates if present
      const savedTop = localStorage.getItem(id + '_spatial_pos');
      let position = [...slot.pos];
      if (savedTop) {
        try { position = JSON.parse(savedTop); } catch(e) {}
      }

      const cssObject = new THREE.CSS3DObject(el);
      cssObject.scale.set(0.18, 0.18, 0.18);
      cssObject.position.set(position[0], position[1], position[2]);
      cssObject.rotation.set(slot.rot[0], slot.rot[1], slot.rot[2]);
      cssScene.add(cssObject);

      panels[id] = {
        obj: cssObject,
        element: el,
        basePos: [...slot.pos],
        baseRot: [...slot.rot],
        isMinimized: false
      };

      setupInteraction(id);
    });

    // Initialize all CSS3D elements to start at 0.18 base scale
    Object.keys(panels).forEach(k => {
      panels[k].obj.scale.set(0.18, 0.18, 0.18);
    });

    window.addEventListener('resize', onWindowResize);
    animate();
  }

  function setupInteraction(id) {
    const data = panels[id];
    const header = data.element.querySelector('.card-header');
    
    // Double click to focus camera
    header.addEventListener('dblclick', (e) => {
      if (e.target.closest('.card-controls')) return;
      focusPanel(id);
    });

    // Simple 3D drag manipulation
    let isDragging = false;
    let prevMouseX = 0, prevMouseY = 0;

    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('.card-controls')) return;
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
      data.element.classList.add('focused');
      // Set focus flag for this element to be on top of others
      Object.keys(panels).forEach(k => {
        if (k !== id) panels[k].element.classList.remove('focused');
      });
      if (window.SoundFX) window.SoundFX.playClick();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      // Translate 2D mouse drag into 3D translation
      data.obj.position.x += deltaX * 0.22;
      data.obj.position.y -= deltaY * 0.22;
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        // Save spatial position
        localStorage.setItem(id + '_spatial_pos', JSON.stringify([
          data.obj.position.x,
          data.obj.position.y,
          data.obj.position.z
        ]));
      }
    });
  }

  function focusPanel(id) {
    const data = panels[id];
    const camera = window.Scene3D.getCamera();
    if (!camera) return;

    if (window.SoundFX) window.SoundFX.playNotification();

    // Smoothly interpolate camera lookAt and position to focus on the window without clipping
    const targetPos = new THREE.Vector3(
      data.obj.position.x,
      data.obj.position.y,
      data.obj.position.z + 130
    );

    let step = 0;
    function smoothCam() {
      if (step < 25) {
        camera.position.lerp(targetPos, 0.15);
        step++;
        requestAnimationFrame(smoothCam);
      }
    }
    smoothCam();
  }

  function toggleMinimize(id) {
    const data = panels[id];
    if (!data) return;

    if (window.SoundFX) window.SoundFX.playClick();

    data.isMinimized = !data.isMinimized;
    data.element.classList.toggle('minimized');

    const targetScale = data.isMinimized ? 0.018 : 0.18;
    let step = 0;

    function scaleTransition() {
      if (step < 10) {
        const cur = data.obj.scale.x;
        const next = cur + (targetScale - cur) * 0.4;
        data.obj.scale.set(next, next, next);
        step++;
        requestAnimationFrame(scaleTransition);
      } else {
        data.obj.scale.set(targetScale, targetScale, targetScale);
      }
    }
    scaleTransition();
  }

  function animate() {
    requestAnimationFrame(animate);
    const camera = window.Scene3D.getCamera();
    const scene = window.Scene3D.getScene();

    if (camera && scene) {
      cssRenderer.render(cssScene, camera);
    }
  }

  function onWindowResize() {
    cssRenderer.setSize(window.innerWidth, window.innerHeight);
  }

  // Export globally
  window.SpatialNodes = {
    init,
    toggleMinimize
  };
})();
