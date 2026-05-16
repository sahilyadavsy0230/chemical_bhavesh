/* ============================================================
   ChemDesignAI — 3D Equipment Visualizer
   Uses Three.js to render interactive 3D equipment models
   ============================================================ */

'use strict';

let _scene, _camera, _renderer, _controls_state, _animFrame;
let _isDragging = false, _prevMouse = { x: 0, y: 0 };
let _rotX = 0.3, _rotY = 0.5;

/**
 * Initialise a Three.js 3D visualizer on a canvas element.
 *
 * @param {string} canvasId  - Canvas element ID
 * @param {string} eqType    - Equipment type key
 * @param {object} dims      - { diameter, length } from backend results
 */
function initVisualizer(canvasId, eqType, dims) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof THREE === 'undefined') return;

  // ── Scene Setup ───────────────────────────────────────────
  _scene = new THREE.Scene();
  _scene.background = new THREE.Color(0x0d1117);
  _scene.fog = new THREE.FogExp2(0x0d1117, 0.05);

  // ── Camera ─────────────────────────────────────────────────
  const W = canvas.clientWidth  || 600;
  const H = canvas.clientHeight || 380;
  _camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
  _camera.position.set(3, 2, 5);
  _camera.lookAt(0, 0, 0);

  // ── Renderer ───────────────────────────────────────────────
  _renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  _renderer.setPixelRatio(window.devicePixelRatio);
  _renderer.setSize(W, H);
  _renderer.shadowMap.enabled = true;
  _renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  // ── Lights ─────────────────────────────────────────────────
  const ambient = new THREE.AmbientLight(0x334477, 0.6);
  _scene.add(ambient);

  const dirLight = new THREE.DirectionalLight(0x88aaff, 1.2);
  dirLight.position.set(5, 10, 7);
  dirLight.castShadow = true;
  _scene.add(dirLight);

  const rimLight = new THREE.DirectionalLight(0x0dcaf0, 0.4);
  rimLight.position.set(-5, 2, -3);
  _scene.add(rimLight);

  // Point light glow
  const pointLight = new THREE.PointLight(0x0d6efd, 0.8, 8);
  pointLight.position.set(0, 2, 0);
  _scene.add(pointLight);

  // ── Grid ───────────────────────────────────────────────────
  const grid = new THREE.GridHelper(10, 20, 0x1a2a3a, 0x111827);
  grid.position.y = -1.5;
  _scene.add(grid);

  // ── Equipment Model ────────────────────────────────────────
  const model = buildEquipmentModel(eqType, dims);
  _scene.add(model);

  // ── Wireframe Overlay ──────────────────────────────────────
  model.traverse(child => {
    if (child.isMesh) {
      const wf = new THREE.LineSegments(
        new THREE.EdgesGeometry(child.geometry),
        new THREE.LineBasicMaterial({ color: 0x0d6efd, transparent: true, opacity: 0.3 })
      );
      child.add(wf);
    }
  });

  // ── Coordinate Axes ────────────────────────────────────────
  const axes = new THREE.AxesHelper(1.5);
  axes.position.set(-2, -1.4, -2);
  _scene.add(axes);

  // ── Mouse Controls ─────────────────────────────────────────
  canvas.addEventListener('mousedown', e => { _isDragging = true; _prevMouse = { x: e.clientX, y: e.clientY }; });
  window.addEventListener('mouseup',   () => { _isDragging = false; });
  window.addEventListener('mousemove', e => {
    if (!_isDragging) return;
    const dx = e.clientX - _prevMouse.x;
    const dy = e.clientY - _prevMouse.y;
    _rotY += dx * 0.008;
    _rotX += dy * 0.008;
    _rotX = Math.max(-Math.PI/2, Math.min(Math.PI/2, _rotX));
    _prevMouse = { x: e.clientX, y: e.clientY };
  });

  // Touch support
  canvas.addEventListener('touchstart', e => {
    _isDragging = true;
    _prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  }, { passive: true });
  canvas.addEventListener('touchmove', e => {
    if (!_isDragging) return;
    const dx = e.touches[0].clientX - _prevMouse.x;
    const dy = e.touches[0].clientY - _prevMouse.y;
    _rotY += dx * 0.008;
    _rotX += dy * 0.008;
    _prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  }, { passive: true });
  canvas.addEventListener('touchend', () => { _isDragging = false; }, { passive: true });

  // Zoom (scroll)
  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    _camera.position.multiplyScalar(1 + e.deltaY * 0.001);
  }, { passive: false });

  // ── Resize Observer ────────────────────────────────────────
  new ResizeObserver(() => {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    _camera.aspect = w / h;
    _camera.updateProjectionMatrix();
    _renderer.setSize(w, h);
  }).observe(canvas);

  // ── Animate ────────────────────────────────────────────────
  (function animate() {
    _animFrame = requestAnimationFrame(animate);

    // Auto-rotate when not dragging
    if (!_isDragging) { _rotY += 0.003; }

    model.rotation.x = _rotX;
    model.rotation.y = _rotY;

    // Pulsing glow
    pointLight.intensity = 0.6 + 0.4 * Math.sin(Date.now() * 0.002);

    _renderer.render(_scene, _camera);
  })();
}

/** Reset camera to default view. */
function resetCamera() {
  _rotX = 0.3;
  _rotY = 0.5;
  if (_camera) {
    _camera.position.set(3, 2, 5);
    _camera.lookAt(0, 0, 0);
  }
}

/* ─────────────────────────────────────────────────────────────
   EQUIPMENT MODEL BUILDERS
   ───────────────────────────────────────────────────────────── */

function buildEquipmentModel(type, dims) {
  const group = new THREE.Group();
  const d = dims.diameter || 0.5;
  const l = dims.length   || 2.0;
  // Normalize for display: target radius 0.5 height 2.0
  const r = Math.min(Math.max(d * 0.8, 0.2), 0.8);
  const h = Math.min(Math.max(l * 0.5, 0.8), 3.0);

  switch (type) {
    case 'heat_exchanger': buildHeatExchanger(group, r, h); break;
    case 'reactor':        buildReactor(group, r, h);       break;
    case 'distillation':   buildDistillation(group, r, h);  break;
    case 'evaporator':     buildEvaporator(group, r, h);    break;
    case 'absorber':       buildAbsorber(group, r, h);      break;
    case 'pump':           buildPump(group);                 break;
    case 'compressor':     buildCompressor(group);           break;
    default:               buildGeneric(group, r, h);       break;
  }
  return group;
}

// ── Shell-and-Tube Heat Exchanger ────────────────────────────
function buildHeatExchanger(group, r, h) {
  const mat = shinyMat(0x4488cc);
  // Shell cylinder
  const shell = mesh(new THREE.CylinderGeometry(r, r, h, 32), mat);
  shell.rotation.z = Math.PI / 2;
  group.add(shell);
  // End caps
  [h/2+0.05, -h/2-0.05].forEach(x => {
    const cap = mesh(new THREE.CylinderGeometry(r*1.05, r*1.05, 0.12, 32), shinyMat(0x2255aa));
    cap.rotation.z = Math.PI / 2;
    cap.position.x = x;
    group.add(cap);
  });
  // Tubes (visible through shell)
  for (let i = 0; i < 7; i++) {
    const angle = (i / 7) * Math.PI * 2;
    const tr = r * 0.55;
    const tube = mesh(
      new THREE.CylinderGeometry(0.04, 0.04, h * 0.9, 12),
      shinyMat(0x88ccff, 0.7)
    );
    tube.rotation.z = Math.PI / 2;
    tube.position.set(0, Math.sin(angle) * tr * 0.5, Math.cos(angle) * tr * 0.5);
    group.add(tube);
  }
  // Nozzles
  addNozzle(group, [0, r + 0.15, h * 0.3], 0x33aaff, 'x');
  addNozzle(group, [0, -r - 0.15, -h * 0.3], 0xff6633, 'x');
}

// ── Reactor Vessel ────────────────────────────────────────────
function buildReactor(group, r, h) {
  const body = mesh(new THREE.CylinderGeometry(r, r * 0.9, h, 32), shinyMat(0x44aa44));
  group.add(body);
  // Ellipsoidal heads
  const head = mesh(new THREE.SphereGeometry(r, 32, 16, 0, Math.PI*2, 0, Math.PI/2), shinyMat(0x338833));
  head.position.y = h / 2;
  group.add(head);
  const bottom = head.clone(); bottom.rotation.x = Math.PI; bottom.position.y = -h / 2;
  group.add(bottom);
  // Agitator shaft
  const shaft = mesh(new THREE.CylinderGeometry(0.03, 0.03, h * 0.9, 8), shinyMat(0xaaaaaa));
  group.add(shaft);
  // Impeller blades
  for (let i = 0; i < 4; i++) {
    const blade = mesh(new THREE.BoxGeometry(r * 0.55, 0.04, 0.1), shinyMat(0x88ccaa));
    blade.rotation.y = (i / 4) * Math.PI * 2;
    blade.position.y = -h * 0.2;
    group.add(blade);
  }
  // Jacket lines
  for (let i = 0; i < 5; i++) {
    const ring = mesh(new THREE.TorusGeometry(r + 0.07, 0.02, 8, 32), shinyMat(0x0099cc));
    ring.position.y = -h * 0.3 + i * h * 0.15;
    group.add(ring);
  }
  addNozzle(group, [0, h/2+0.35, 0], 0xaaffaa, 'y');
  addNozzle(group, [r+0.12, 0, 0], 0x00ccff, 'z');
}

// ── Distillation Column ───────────────────────────────────────
function buildDistillation(group, r, h) {
  const col = mesh(new THREE.CylinderGeometry(r, r, h * 2, 32), shinyMat(0xaa8844));
  group.add(col);
  // Trays
  for (let i = 0; i < 6; i++) {
    const tray = mesh(new THREE.CylinderGeometry(r*0.98, r*0.98, 0.04, 32), shinyMat(0x886633));
    tray.position.y = -h + i * (h * 2 / 5);
    group.add(tray);
  }
  // Condenser at top
  const cond = mesh(new THREE.BoxGeometry(r*1.5, r*0.8, r*1.2), shinyMat(0x4488aa));
  cond.position.y = h + r * 0.5;
  group.add(cond);
  // Reboiler at bottom
  const reb = mesh(new THREE.BoxGeometry(r*1.6, r*0.7, r*1.3), shinyMat(0xaa4433));
  reb.position.y = -(h + r * 0.45);
  group.add(reb);
  addNozzle(group, [r+0.12, 0, 0], 0xffcc44, 'z');
  addNozzle(group, [0, h+0.3, 0], 0x44ccff, 'y');
}

// ── Evaporator ────────────────────────────────────────────────
function buildEvaporator(group, r, h) {
  const body = mesh(new THREE.CylinderGeometry(r, r * 0.8, h, 32), shinyMat(0xcc7722));
  group.add(body);
  // Heating element tubes at bottom
  for (let i = 0; i < 6; i++) {
    const angle = (i / 6) * Math.PI * 2;
    const tube = mesh(new THREE.CylinderGeometry(0.05, 0.05, h * 0.4, 8), shinyMat(0xff5500));
    tube.position.set(Math.cos(angle) * r * 0.6, -h * 0.25, Math.sin(angle) * r * 0.6);
    group.add(tube);
  }
  // Vapor dome
  const dome = mesh(new THREE.SphereGeometry(r, 32, 16, 0, Math.PI*2, 0, Math.PI/2), shinyMat(0xdd9933));
  dome.position.y = h / 2;
  group.add(dome);
  // Vapor pipe
  const vpipe = mesh(new THREE.CylinderGeometry(r*0.25, r*0.25, h*0.5, 16), shinyMat(0x4488cc));
  vpipe.position.y = h * 0.9;
  group.add(vpipe);
}

// ── Absorber (Packed Column) ──────────────────────────────────
function buildAbsorber(group, r, h) {
  const body = mesh(new THREE.CylinderGeometry(r, r, h * 2, 32), shinyMat(0x226688));
  group.add(body);
  // Packing (random spheres inside)
  for (let i = 0; i < 20; i++) {
    const ps = mesh(new THREE.SphereGeometry(r * 0.12, 6, 6), shinyMat(0x4499bb, 0.5));
    ps.position.set(
      (Math.random() - 0.5) * r * 1.5,
      (Math.random() - 0.5) * h * 1.5,
      (Math.random() - 0.5) * r * 1.5
    );
    group.add(ps);
  }
  // Support grids
  [h*0.5, -h*0.5].forEach(y => {
    const grid = mesh(new THREE.CylinderGeometry(r*0.97, r*0.97, 0.06, 32), shinyMat(0x335566));
    grid.position.y = y;
    group.add(grid);
  });
  addNozzle(group, [0, h+0.2, 0], 0x44ccff, 'y');     // gas out / liquid in
  addNozzle(group, [0, -(h+0.2), 0], 0x44ff88, 'y');  // liquid out / gas in
  addNozzle(group, [r+0.12, h*0.8, 0], 0xaaddff, 'z');
}

// ── Centrifugal Pump ──────────────────────────────────────────
function buildPump(group) {
  // Casing (volute approximated as flattened sphere)
  const casing = mesh(new THREE.SphereGeometry(0.5, 32, 16), shinyMat(0x888888));
  casing.scale.z = 0.55;
  group.add(casing);
  // Impeller
  for (let i = 0; i < 5; i++) {
    const blade = mesh(new THREE.BoxGeometry(0.35, 0.05, 0.08), shinyMat(0x4499cc));
    blade.rotation.z = (i / 5) * Math.PI * 2;
    group.add(blade);
  }
  // Motor
  const motor = mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.8, 32), shinyMat(0x444444));
  motor.rotation.z = Math.PI / 2;
  motor.position.x = 0.8;
  group.add(motor);
  // Shaft coupling
  const coupling = mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.25, 16), shinyMat(0xffcc00));
  coupling.rotation.z = Math.PI / 2;
  coupling.position.x = 0.42;
  group.add(coupling);
  // Discharge nozzle
  addNozzle(group, [0, 0.65, 0], 0x4499cc, 'y');
  addNozzle(group, [-0.65, 0, 0], 0x44ccff, 'x');
}

// ── Compressor ───────────────────────────────────────────────
function buildCompressor(group) {
  // Main casing
  const casing = mesh(new THREE.CylinderGeometry(0.5, 0.55, 1.0, 32), shinyMat(0x555566));
  casing.rotation.z = Math.PI / 2;
  group.add(casing);
  // Stages
  [0.6, 0.3, 0].forEach((x, i) => {
    const stage = mesh(new THREE.CylinderGeometry(0.42 - i*0.06, 0.42 - i*0.06, 0.28, 24), shinyMat(0x6677aa));
    stage.rotation.z = Math.PI / 2;
    stage.position.x = x - 0.45;
    group.add(stage);
  });
  // Rotor disk
  const rotor = mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.1, 32), shinyMat(0x0d6efd));
  rotor.rotation.z = Math.PI / 2;
  group.add(rotor);
  // Inlet/outlet
  addNozzle(group, [0.7, 0, 0], 0x44ccff, 'x');
  addNozzle(group, [-0.7, 0, 0], 0xff6644, 'x');
  // Intercooler
  const ic = mesh(new THREE.BoxGeometry(0.6, 0.3, 0.2), shinyMat(0x336688));
  ic.position.set(0, 0.8, 0);
  group.add(ic);
}

// ── Generic ────────────────────────────────────────────────────
function buildGeneric(group, r, h) {
  const body = mesh(new THREE.CylinderGeometry(r, r, h, 32), shinyMat(0x5588bb));
  group.add(body);
}

/* ─────────────────────────────────────────────────────────────
   HELPERS
   ───────────────────────────────────────────────────────────── */
function mesh(geo, mat) {
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = m.receiveShadow = true;
  return m;
}

function shinyMat(color, opacity = 1) {
  return new THREE.MeshPhongMaterial({
    color, opacity,
    transparent: opacity < 1,
    shininess: 120,
    specular: new THREE.Color(0x224466),
  });
}

function addNozzle(group, pos, color, axis) {
  const nozzle = mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.25, 12), shinyMat(color));
  if (axis === 'x') nozzle.rotation.z = Math.PI / 2;
  if (axis === 'z') nozzle.rotation.x = Math.PI / 2;
  nozzle.position.set(...pos);
  group.add(nozzle);
  // Flange
  const flange = mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.04, 12), shinyMat(0x445566));
  if (axis === 'x') flange.rotation.z = Math.PI / 2;
  if (axis === 'z') flange.rotation.x = Math.PI / 2;
  flange.position.set(
    pos[0] + (axis==='x' ? 0.12 : 0),
    pos[1] + (axis==='y' ? 0.12 : 0),
    pos[2] + (axis==='z' ? 0.12 : 0)
  );
  group.add(flange);
}

// Expose globals
window.initVisualizer = initVisualizer;
window.resetCamera    = resetCamera;
