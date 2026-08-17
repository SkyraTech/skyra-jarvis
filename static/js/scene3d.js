// ══════════════════════════════════════════════════════════════════════════════
// JARVIS 3D WebGL Core — Fresnel Glow Quantum Mind Core (scene3d.js)
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

  // Emissive color maps for Fresnel state reactivity
  const stateColors = {
    idle: "#06b6d4",            // Cyan
    listening: "#06b6d4",       // Cyan
    thinking: "#a855f7",        // Violet
    speaking: "#10b981",        // Emerald
    tool_executing: "#f59e0b",  // Amber
    error: "#ef4444",           // Red
    offline: "#3a3a3a"          // Off/Gray
  };

  // Custom vertex shader for Fresnel effect
  const vertexShader = `
    varying vec3 vNormal;
    varying vec3 vViewPosition;
    void main() {
      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      vNormal = normalize(normalMatrix * normal);
      vViewPosition = -mvPosition.xyz;
      gl_Position = projectionMatrix * mvPosition;
    }
  `;

  // Custom fragment shader for Fresnel + scanline + Chromatic Aberration glow
  const fragmentShader = `
    uniform vec3 glowColor;
    uniform float time;
    uniform float pulseIntensity;
    varying vec3 vNormal;
    varying vec3 vViewPosition;
    void main() {
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vViewPosition);
      
      // Basic Fresnel glow factor
      float intensity = pow(1.0 - dot(normal, viewDir), 2.2) * 1.5;
      
      // Horizontal shader scanlines moving downwards
      float scanline = sin(vViewPosition.y * 1.8 - time * 6.0) * 0.15 + 0.85;
      
      // Apply pulsing factor
      vec3 color = glowColor * intensity * scanline * pulseIntensity;
      
      gl_FragColor = vec4(color, intensity * 0.45);
    }
  `;

  function init() {
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x020100, 0.0015);

    camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 1, 2000);
    camera.position.set(0, 30, 200);
    camera.lookAt(0, 10, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    // 1. Grid scroll
    const gridHelper = new THREE.GridHelper(480, 48, 0xff7c00, 0x221000);
    gridHelper.position.y = -35;
    scene.add(gridHelper);
    grid = gridHelper;

    // 2. Starfield
    buildStarField();

    // 3. Three.js Fresnel Glow Holographic Core (replace yellow particle mind)
    buildFresnelCore();

    // 4. Atomic orbitals
    buildAtomicOrbitals();

    // 5. Scene Lighting
    scene.add(new THREE.AmbientLight(0x1a0f02, 2.0));
    const dirLight = new THREE.DirectionalLight(0xff9f00, 3.5);
    dirLight.position.set(0, 180, 60);
    scene.add(dirLight);

    window.addEventListener('resize', onWindowResize);
    window.addEventListener('mousemove', onMouseMove);

    animate();
  }

  function buildStarField() {
    const starCount = 1200;
    const geom = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 1200;
      positions[i * 3 + 1] = Math.random() * 600 - 150;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 1200;
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: 0x06b6d4,
      size: 0.65,
      transparent: true,
      opacity: 0.28
    });

    starField = new THREE.Points(geom, material);
    scene.add(starField);
  }

  function buildFresnelCore() {
    // Holographic Energy Inner Core Sphere (Icosahedron for sci-fi structural nodes)
    const geom = new THREE.IcosahedronGeometry(22, 3);
    
    // ShaderMaterial exposing custom Fresnel uniform binds
    const material = new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(stateColors.idle) },
        time: { value: 0.0 },
        pulseIntensity: { value: 1.0 }
      },
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
      transparent: true,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide
    });

    brainCore = new THREE.Mesh(geom, material);
    brainCore.position.y = 12;
    scene.add(brainCore);

    // Inner wireframe shell skeleton mapping
    const wireGeom = new THREE.IcosahedronGeometry(22.2, 2);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      wireframe: true,
      transparent: true,
      opacity: 0.15
    });
    synapseLines = new THREE.Mesh(wireGeom, wireMat);
    synapseLines.position.y = 12;
    scene.add(synapseLines);
  }

  function buildAtomicOrbitals() {
    const ringRadii = [38, 48, 58];
    const ringColors = [0x06b6d4, 0x0891b2, 0x0891b2];

    for (let i = 0; i < 3; i++) {
      const ringGeom = new THREE.TorusGeometry(ringRadii[i], 0.2, 8, 80);
      const ringMat = new THREE.MeshBasicMaterial({
        color: ringColors[i],
        transparent: true,
        opacity: 0.14
      });
      const orbitalRing = new THREE.Mesh(ringGeom, ringMat);
      orbitalRing.position.y = 12;
      orbitalRing.rotation.x = Math.PI / 3 * (i + 1);
      orbitalRing.rotation.y = Math.PI / 4 * (i + 1);
      scene.add(orbitalRing);
      orbitRings.push(orbitalRing);

      // Orbiting electron mesh
      const electronGeom = new THREE.SphereGeometry(1.4, 8, 8);
      const electronMat = new THREE.MeshBasicMaterial({
        color: ringColors[i],
        transparent: true,
        opacity: 0.9
      });
      const electron = new THREE.Mesh(electronGeom, electronMat);
      scene.add(electron);

      electrons.push({
        mesh: electron,
        radius: ringRadii[i],
        angle: Math.random() * Math.PI * 2,
        speed: 0.010 * (i + 1),
        parentRing: orbitalRing
      });
    }
  }

  function updateCoreColors(hexColor) {
    const newColor = new THREE.Color(hexColor);
    
    // Update Shader uniforms
    if (brainCore && brainCore.material.uniforms) {
      brainCore.material.uniforms.glowColor.value.copy(newColor);
    }
    if (synapseLines) {
      synapseLines.material.color.copy(newColor);
    }
    orbitRings.forEach(ring => {
      ring.material.color.copy(newColor);
    });
    electrons.forEach(ele => {
      ele.mesh.material.color.copy(newColor);
    });
    if (starField) {
      starField.material.color.copy(newColor);
    }
  }

  function animate() {
    requestAnimationFrame(animate);
    time += 0.015;

    // 1. Grid scroll
    if (grid) {
      grid.position.z += 0.55;
      if (grid.position.z > 10.0) grid.position.z = 0;
    }

    // 2. Background stars rotation
    if (starField) {
      starField.rotation.y += 0.0002;
    }

    // 3. Shader time increment
    if (brainCore && brainCore.material.uniforms) {
      brainCore.material.uniforms.time.value = time;
    }

    // 4. Core rotation
    if (brainCore) {
      brainCore.rotation.y += 0.004;
      brainCore.rotation.x = Math.sin(time * 0.3) * 0.15;
    }
    if (synapseLines) {
      synapseLines.rotation.y -= 0.002;
    }

    // 5. Electrons orbit
    electrons.forEach((ele) => {
      let speedMod = 1.0;
      if (systemState === "thinking") speedMod = 2.0;
      else if (systemState === "tool_executing") speedMod = 2.8;

      ele.angle += ele.speed * speedMod;

      const localX = ele.radius * Math.cos(ele.angle);
      const localZ = ele.radius * Math.sin(ele.angle);
      const posVec = new THREE.Vector3(localX, 0, localZ);
      posVec.applyEuler(ele.parentRing.rotation);
      ele.mesh.position.copy(posVec);
      ele.mesh.position.y += 12;
    });

    // 6. Gyroscopic rings scaling
    let targetRingScale = 1.0;
    if (systemState === "thinking") {
      targetRingScale = 1.25 + Math.sin(time * 15) * 0.03;
    } else if (systemState === "tool_executing") {
      targetRingScale = 1.3 + Math.sin(time * 25) * 0.05;
    } else if (systemState === "speaking") {
      targetRingScale = 1.1 + Math.cos(time * 8) * 0.03;
    }

    orbitRings.forEach((ring, index) => {
      const currentScale = ring.scale.x;
      const nextScale = currentScale + (targetRingScale - currentScale) * 0.08;
      ring.scale.set(nextScale, nextScale, nextScale);
      electrons[index].radius = (38 + (index * 10)) * nextScale;
      ring.rotation.z += 0.0025 * (index + 1);
    });

    // 7. Pulse scale & Fresnel glow uniforms
    if (systemState === "speaking") {
      targetPulseScale = 1.0 + Math.sin(time * 20) * 0.06;
      if (brainCore && brainCore.material.uniforms) {
        brainCore.material.uniforms.pulseIntensity.value = 1.3 + Math.sin(time * 20) * 0.3;
      }
    } else if (systemState === "listening") {
      targetPulseScale = 1.02 + Math.sin(time * 8) * 0.03;
      if (brainCore && brainCore.material.uniforms) {
        brainCore.material.uniforms.pulseIntensity.value = 1.1;
      }
    } else if (systemState === "thinking") {
      targetPulseScale = 1.08 + Math.sin(time * 30) * 0.1;
      if (brainCore && brainCore.material.uniforms) {
        brainCore.material.uniforms.pulseIntensity.value = 1.4 + Math.sin(time * 30) * 0.4;
      }
    } else if (systemState === "tool_executing") {
      targetPulseScale = 1.12 + Math.sin(time * 40) * 0.12;
      if (brainCore && brainCore.material.uniforms) {
        brainCore.material.uniforms.pulseIntensity.value = 1.6 + Math.sin(time * 40) * 0.5;
      }
    } else {
      targetPulseScale = 1.0 + Math.sin(time * 2) * 0.015;
      if (brainCore && brainCore.material.uniforms) {
        brainCore.material.uniforms.pulseIntensity.value = 1.0;
      }
    }

    pulseScale += (targetPulseScale - pulseScale) * 0.08;
    if (brainCore) brainCore.scale.set(pulseScale, pulseScale, pulseScale);
    if (synapseLines) synapseLines.scale.set(pulseScale * 1.01, pulseScale * 1.01, pulseScale * 1.01);

    // Mouse parallax
    camera.position.x += (mouseX * 25 - camera.position.x) * 0.04;
    camera.position.y += (mouseY * 15 + 30 - camera.position.y) * 0.04;
    camera.lookAt(0, 10, 0);

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
      updateCoreColors(color);
      document.documentElement.style.setProperty('--state-color', color);
      document.documentElement.style.setProperty('--state-glow', color + '59');
      document.documentElement.style.setProperty('--state-dim', color + '14');
    }
  };
})();
