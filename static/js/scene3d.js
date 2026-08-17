// ══════════════════════════════════════════════════════════════════════════════
// JARVIS 3D WebGL Core — Scene Initialization & Render Loop (scene3d.js)
// ══════════════════════════════════════════════════════════════════════════════

(function() {
  const container = document.getElementById('canvas-container');
  let scene, camera, renderer, grid, brainCore, synapseLines, starField;
  let orbitRings = [], electrons = [];
  let systemState = "idle";
  let time = 0;
  let pulseScale = 1.0;
  let targetPulseScale = 1.0;
  let mouseX = 0, mouseY = 0;

  // State colors corresponding to theme CSS tokens
  const stateColors = {
    idle: "#ff8400",
    listening: "#ff9d00",
    thinking: "#a855f7",
    speaking: "#10b981",
    tool_executing: "#06b6d4",
    error: "#ef4444",
    offline: "#3a3a3a"
  };

  function init() {
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030200, 0.0015);

    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 2000);
    camera.position.set(0, 45, 200);
    camera.lookAt(0, 15, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    container.appendChild(renderer.domElement);

    // 1. Ground helper grid (Synthwave flying grid)
    const gridHelper = new THREE.GridHelper(480, 44, 0xff7c00, 0x3d1c00);
    gridHelper.position.y = -35;
    scene.add(gridHelper);
    grid = gridHelper;

    // 2. Starfield background
    buildStarField();

    // 3. Multi-layer Neural Synapses Mind Core
    buildNeuralSynapses();

    // 4. Atomic Orbitals (Bohr style gyroscope rings)
    buildAtomicOrbitals();

    // 5. Scene Lights
    const ambient = new THREE.AmbientLight(0x2d1700, 2.0);
    scene.add(ambient);

    const directLight = new THREE.DirectionalLight(0xff9f00, 3.0);
    directLight.position.set(0, 150, 50);
    scene.add(directLight);

    // Events
    window.addEventListener('resize', onWindowResize);
    window.addEventListener('mousemove', onMouseMove);

    animate();
  }

  function buildStarField() {
    const starCount = 1500;
    const geom = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 1200;
      positions[i * 3 + 1] = Math.random() * 500 - 100;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 1200;
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: 0xffaa00,
      size: 0.8,
      transparent: true,
      opacity: 0.35
    });

    starField = new THREE.Points(geom, material);
    scene.add(starField);
  }

  function buildNeuralSynapses() {
    const synapseCount = 900;
    const geom = new THREE.BufferGeometry();
    const positions = new Float32Array(synapseCount * 3);
    const colors = new Float32Array(synapseCount * 3);
    const baseColor = new THREE.Color(stateColors.idle);

    for (let i = 0; i < synapseCount; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 26 + (Math.random() * 8);

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) + 15;
      positions[i * 3 + 2] = r * Math.cos(phi);

      colors[i * 3] = baseColor.r;
      colors[i * 3 + 1] = baseColor.g;
      colors[i * 3 + 2] = baseColor.b;
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 2.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.85
    });

    brainCore = new THREE.Points(geom, material);
    scene.add(brainCore);

    // Connections (synaptic lines)
    const linePositions = [];
    const posAttr = geom.attributes.position;
    for (let i = 0; i < synapseCount; i += 2) {
      const idx1 = i;
      const idx2 = (i + Math.floor(Math.random() * 18) + 1) % synapseCount;
      linePositions.push(
        posAttr.getX(idx1), posAttr.getY(idx1), posAttr.getZ(idx1),
        posAttr.getX(idx2), posAttr.getY(idx2), posAttr.getZ(idx2)
      );
    }

    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    const lineMat = new THREE.LineBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.22
    });

    synapseLines = new THREE.LineSegments(lineGeom, lineMat);
    scene.add(synapseLines);
  }

  function buildAtomicOrbitals() {
    const ringRadii = [40, 50, 60];
    const ringColors = [0xffaa00, 0xff7c00, 0xffea00];

    for (let i = 0; i < 3; i++) {
      const ringGeom = new THREE.TorusGeometry(ringRadii[i], 0.25, 8, 100);
      const ringMat = new THREE.MeshBasicMaterial({
        color: ringColors[i],
        transparent: true,
        opacity: 0.18
      });
      const orbitalRing = new THREE.Mesh(ringGeom, ringMat);
      orbitalRing.position.y = 15;
      orbitalRing.rotation.x = Math.PI / 3 * (i + 1);
      orbitalRing.rotation.y = Math.PI / 4 * (i + 1);
      scene.add(orbitalRing);
      orbitRings.push(orbitalRing);

      // Electron particle
      const electronGeom = new THREE.SphereGeometry(1.8, 8, 8);
      const electronMat = new THREE.MeshBasicMaterial({
        color: ringColors[i],
        transparent: true,
        opacity: 0.95
      });
      const electron = new THREE.Mesh(electronGeom, electronMat);
      scene.add(electron);

      electrons.push({
        mesh: electron,
        radius: ringRadii[i],
        angle: Math.random() * Math.PI * 2,
        speed: 0.012 * (i + 1),
        parentRing: orbitalRing
      });
    }
  }

  function updateBrainColors(hexColor) {
    const newColor = new THREE.Color(hexColor);
    if (synapseLines) synapseLines.material.color = newColor;
    if (brainCore) {
      const colors = brainCore.geometry.attributes.color.array;
      for (let i = 0; i < colors.length / 3; i++) {
        colors[i * 3] = newColor.r;
        colors[i * 3 + 1] = newColor.g;
        colors[i * 3 + 2] = newColor.b;
      }
      brainCore.geometry.attributes.color.needsUpdate = true;
    }
    orbitRings.forEach(ring => {
      ring.material.color = newColor;
    });
    electrons.forEach(ele => {
      ele.mesh.material.color = newColor;
    });
  }

  function animate() {
    requestAnimationFrame(animate);
    time += 0.02;

    // 1. Grid scroll
    if (grid) {
      grid.position.z += 0.65;
      if (grid.position.z > 10.9) grid.position.z = 0;
    }

    // 2. Stars drift
    if (starField) {
      starField.rotation.y += 0.0003;
    }

    // 3. Brain rotate
    if (brainCore) {
      brainCore.rotation.y += 0.0035;
      brainCore.rotation.z = Math.sin(time * 0.4) * 0.025;
    }
    if (synapseLines) {
      synapseLines.rotation.y += 0.0035;
      synapseLines.rotation.z = Math.sin(time * 0.4) * 0.025;
    }

    // 4. Electrons orbit
    electrons.forEach((ele) => {
      let speedMod = 1.0;
      if (systemState === "thinking") speedMod = 2.0;
      else if (systemState === "tool_executing") speedMod = 2.5;

      ele.angle += ele.speed * speedMod;

      const localX = ele.radius * Math.cos(ele.angle);
      const localZ = ele.radius * Math.sin(ele.angle);
      const posVec = new THREE.Vector3(localX, 0, localZ);
      posVec.applyEuler(ele.parentRing.rotation);
      ele.mesh.position.copy(posVec);
      ele.mesh.position.y += 15;
    });

    // 5. Gyro rings scale
    let targetRingScale = 1.0;
    if (systemState === "thinking") {
      targetRingScale = 1.28 + Math.sin(time * 18) * 0.04;
      synapseLines.material.opacity = 0.55 + Math.sin(time * 25) * 0.25;
    } else if (systemState === "tool_executing") {
      targetRingScale = 1.35 + Math.sin(time * 30) * 0.06;
      synapseLines.material.opacity = 0.7;
    } else if (systemState === "speaking") {
      targetRingScale = 1.15 + Math.cos(time * 10) * 0.04;
      synapseLines.material.opacity = 0.45;
    } else {
      targetRingScale = 1.0;
      synapseLines.material.opacity = 0.22;
    }

    orbitRings.forEach((ring, index) => {
      const currentScale = ring.scale.x;
      const nextScale = currentScale + (targetRingScale - currentScale) * 0.08;
      ring.scale.set(nextScale, nextScale, nextScale);
      electrons[index].radius = (40 + (index * 10)) * nextScale;
      ring.rotation.z += 0.002 * (index + 1);
    });

    // 6. Pulse scale
    if (systemState === "speaking") {
      targetPulseScale = 1.0 + Math.sin(time * 24) * 0.08;
      brainCore.material.size = 2.6 + Math.sin(time * 18) * 0.5;
    } else if (systemState === "listening") {
      targetPulseScale = 1.05 + Math.sin(time * 10) * 0.04;
      brainCore.material.size = 2.4;
    } else if (systemState === "thinking") {
      targetPulseScale = 1.1 + Math.sin(time * 35) * 0.12;
      brainCore.material.size = 3.0;
    } else if (systemState === "tool_executing") {
      targetPulseScale = 1.15 + Math.sin(time * 45) * 0.15;
      brainCore.material.size = 3.2;
    } else {
      targetPulseScale = 1.0 + Math.sin(time * 2) * 0.015;
      brainCore.material.size = 1.8;
    }

    pulseScale += (targetPulseScale - pulseScale) * 0.08;
    if (brainCore) brainCore.scale.set(pulseScale, pulseScale, pulseScale);
    if (synapseLines) synapseLines.scale.set(pulseScale, pulseScale, pulseScale);

    // Camera parallax
    camera.position.x += (mouseX * 35 - camera.position.x) * 0.03;
    camera.position.y += (mouseY * 20 + 45 - camera.position.y) * 0.03;
    camera.lookAt(0, 15, 0);

    renderer.render(scene, camera);
  }

  function onMouseMove(e) {
    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
  }

  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  // Export globally
  window.Scene3D = {
    init,
    getScene: () => scene,
    getCamera: () => camera,
    getRenderer: () => renderer,
    updateState: (state) => {
      systemState = state;
      const color = stateColors[state] || stateColors.idle;
      updateBrainColors(color);
      document.documentElement.style.setProperty('--state-color', color);
      document.documentElement.style.setProperty('--state-glow', color + '59');
      document.documentElement.style.setProperty('--state-dim', color + '14');
    }
  };
})();
