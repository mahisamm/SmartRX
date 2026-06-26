import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

/**
 * ThreeBackground — a premium DNA double-helix backdrop for the login screen.
 * Glossy backbones (warm + cool tint), alternating teal/amber base-pair rungs,
 * bright "energy" glints that race up both strands, and faint ambient motes.
 * Slowly turns, gently bobs, parallaxes toward the pointer. Self-cleans.
 */
export default function ThreeBackground() {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    } catch {
      return undefined;
    }

    let width = mount.clientWidth || window.innerWidth;
    let height = mount.clientHeight || window.innerHeight;

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0xffffff, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xffffff, 0.038);

    const pmrem = new THREE.PMREMGenerator(renderer);
    const envScene = new RoomEnvironment();
    const envRT = pmrem.fromScene(envScene, 0.04);
    scene.environment = envRT.texture;

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    camera.position.set(0, 0, 18);

    // Lights — bright key from top-right, soft rim from opposite
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(8, 12, 10);
    key.castShadow = true;
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xe8eef5, 0.7);
    rim.position.set(-8, -6, -8);
    scene.add(rim);
    const fill = new THREE.DirectionalLight(0xf0f4ff, 0.4);
    fill.position.set(0, -10, 8);
    scene.add(fill);

    // Materials — glossy, lightly tinted backbones (warm strand + cool strand)
    const strandWarm = new THREE.MeshPhysicalMaterial({
      color: 0xf0cdd6, roughness: 0.14, metalness: 0.85,
      clearcoat: 1.0, clearcoatRoughness: 0.08, envMapIntensity: 1.4, reflectivity: 1.0,
    });
    const strandCool = new THREE.MeshPhysicalMaterial({
      color: 0xc9d8ec, roughness: 0.14, metalness: 0.85,
      clearcoat: 1.0, clearcoatRoughness: 0.08, envMapIntensity: 1.4, reflectivity: 1.0,
    });
    // base-pair rungs alternate teal / amber and glow a little
    const rungTeal = new THREE.MeshPhysicalMaterial({
      color: 0x0ea5a4, roughness: 0.3, metalness: 0.4,
      emissive: 0x0ea5a4, emissiveIntensity: 0.22, clearcoat: 0.5, envMapIntensity: 1.0,
    });
    const rungAmber = new THREE.MeshPhysicalMaterial({
      color: 0xf59e0b, roughness: 0.3, metalness: 0.4,
      emissive: 0xf59e0b, emissiveIntensity: 0.22, clearcoat: 0.5, envMapIntensity: 1.0,
    });
    const jointMat = new THREE.MeshPhysicalMaterial({
      color: 0xc8cfd8, roughness: 0.1, metalness: 0.9,
      clearcoat: 1.0, clearcoatRoughness: 0.06, envMapIntensity: 1.5,
    });

    const PAIRS = 26;
    const RADIUS = 3.0;
    const TURN = 0.52;
    const STEP = 0.82;
    const ySpan = (PAIRS - 1) * STEP;

    // continuous helix point for a strand (phase 0 = strand A, PI = strand B)
    const helixPoint = (s, phase, out) => {
      const angle = s * TURN + phase;
      out.set(Math.cos(angle) * RADIUS, s * STEP - ySpan / 2, Math.sin(angle) * RADIUS);
      return out;
    };

    const nodeGeo = new THREE.SphereGeometry(0.46, 40, 40);
    const jointGeo = new THREE.SphereGeometry(0.18, 24, 24);
    const Y_AXIS = new THREE.Vector3(0, 1, 0);
    const tmpDir = new THREE.Vector3();
    const tmpQuat = new THREE.Quaternion();
    const rungGeos = [];

    const helix = new THREE.Group();
    scene.add(helix);

    for (let i = 0; i < PAIRS; i++) {
      const angle = i * TURN;
      const y = i * STEP - ySpan / 2;

      const ax = Math.cos(angle) * RADIUS;
      const az = Math.sin(angle) * RADIUS;
      const bx = Math.cos(angle + Math.PI) * RADIUS;
      const bz = Math.sin(angle + Math.PI) * RADIUS;

      // Backbone spheres — warm strand + cool strand
      const a = new THREE.Mesh(nodeGeo, strandWarm);
      a.position.set(ax, y, az);
      a.castShadow = true;
      const b = new THREE.Mesh(nodeGeo, strandCool);
      b.position.set(bx, y, bz);
      b.castShadow = true;
      helix.add(a, b);

      // Rung — alternating teal / amber base pair
      const dx = bx - ax, dz = bz - az;
      const len = Math.sqrt(dx * dx + dz * dz);
      const rungGeo = new THREE.CylinderGeometry(0.085, 0.085, len, 16);
      rungGeos.push(rungGeo);
      const rung = new THREE.Mesh(rungGeo, i % 2 ? rungAmber : rungTeal);
      rung.position.set((ax + bx) / 2, y, (az + bz) / 2);
      tmpDir.set(dx, 0, dz);
      tmpQuat.setFromUnitVectors(Y_AXIS, tmpDir.normalize());
      rung.quaternion.copy(tmpQuat);
      rung.castShadow = true;
      helix.add(rung);

      // Small joint spheres where rung meets backbone
      const ja = new THREE.Mesh(jointGeo, jointMat);
      ja.position.set(ax + dx * 0.12, y, az + dz * 0.12);
      const jb = new THREE.Mesh(jointGeo, jointMat);
      jb.position.set(bx - dx * 0.12, y, bz - dz * 0.12);
      helix.add(ja, jb);
    }

    helix.rotation.z = 0.18;
    helix.rotation.x = 0.06;

    // ── soft round glow sprite (for energy glints + motes) ──
    const makeGlow = () => {
      const c = document.createElement("canvas");
      c.width = c.height = 64;
      const ctx = c.getContext("2d");
      const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      g.addColorStop(0.0, "rgba(255,255,255,1)");
      g.addColorStop(0.4, "rgba(255,255,255,0.7)");
      g.addColorStop(1.0, "rgba(255,255,255,0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 64, 64);
      const tex = new THREE.CanvasTexture(c);
      tex.colorSpace = THREE.SRGBColorSpace;
      return tex;
    };
    const sprite = makeGlow();

    // ── energy glints racing up both strands ──
    const GLINTS = 8; // 4 per strand
    const glints = [];
    const glintCol = new THREE.Color(0xf43f5e);
    const glintColB = new THREE.Color(0x3b82f6);
    const gPos = new Float32Array(GLINTS * 3);
    const gCol = new Float32Array(GLINTS * 3);
    for (let i = 0; i < GLINTS; i++) {
      const strandA = i % 2 === 0;
      glints.push({ phase: strandA ? 0 : Math.PI, s: Math.random() * (PAIRS - 1), speed: 3 + Math.random() * 2.5 });
      const c = strandA ? glintCol : glintColB;
      gCol[i * 3] = c.r; gCol[i * 3 + 1] = c.g; gCol[i * 3 + 2] = c.b;
    }
    const glintGeo = new THREE.BufferGeometry();
    glintGeo.setAttribute("position", new THREE.BufferAttribute(gPos, 3));
    glintGeo.setAttribute("color", new THREE.BufferAttribute(gCol, 3));
    const glintMat = new THREE.PointsMaterial({
      size: 0.95, map: sprite, vertexColors: true, transparent: true,
      depthWrite: false, sizeAttenuation: true, opacity: 0.95, blending: THREE.NormalBlending,
    });
    const glintPoints = new THREE.Points(glintGeo, glintMat);
    helix.add(glintPoints);

    // ── faint ambient motes drifting around the helix ──
    const MOTES = 90;
    const mPos = new Float32Array(MOTES * 3);
    const mVel = new Float32Array(MOTES);
    for (let i = 0; i < MOTES; i++) {
      const r = RADIUS * (1.1 + Math.random() * 1.3);
      const a = Math.random() * Math.PI * 2;
      mPos[i * 3] = Math.cos(a) * r;
      mPos[i * 3 + 1] = (Math.random() - 0.5) * ySpan * 1.2;
      mPos[i * 3 + 2] = Math.sin(a) * r;
      mVel[i] = 0.15 + Math.random() * 0.4;
    }
    const moteGeo = new THREE.BufferGeometry();
    moteGeo.setAttribute("position", new THREE.BufferAttribute(mPos, 3));
    const moteMat = new THREE.PointsMaterial({
      size: 0.22, map: sprite, color: 0x94a3b8, transparent: true,
      depthWrite: false, sizeAttenuation: true, opacity: 0.4, blending: THREE.NormalBlending,
    });
    const motePoints = new THREE.Points(moteGeo, moteMat);
    helix.add(motePoints);

    const disposables = [nodeGeo, jointGeo, ...rungGeos, strandWarm, strandCool, rungTeal, rungAmber, jointMat, glintGeo, glintMat, moteGeo, moteMat, sprite];

    // Pointer parallax
    const pointer = { x: 0, y: 0 };
    const target = { x: 0, y: 0 };
    const onPointerMove = (e) => {
      target.x = (e.clientX / window.innerWidth - 0.5) * 2;
      target.y = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("pointermove", onPointerMove);

    // Resize
    const resize = () => {
      width = mount.clientWidth || window.innerWidth;
      height = mount.clientHeight || window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    const ro = new ResizeObserver(resize);
    ro.observe(mount);

    const clock = new THREE.Clock();
    const tmp = new THREE.Vector3();
    let frameId = 0;
    let running = true;

    const renderFrame = () => {
      const dt = Math.min(clock.getDelta(), 0.05);
      const t = clock.elapsedTime;
      helix.rotation.y = t * 0.18;
      helix.position.y = Math.sin(t * 0.35) * 0.28;

      // advance energy glints up the strands
      const gAttr = glintGeo.attributes.position;
      for (let i = 0; i < GLINTS; i++) {
        const gl = glints[i];
        gl.s += gl.speed * dt;
        if (gl.s > PAIRS - 1) gl.s -= PAIRS - 1;
        helixPoint(gl.s, gl.phase, tmp);
        gAttr.array[i * 3] = tmp.x;
        gAttr.array[i * 3 + 1] = tmp.y;
        gAttr.array[i * 3 + 2] = tmp.z;
      }
      gAttr.needsUpdate = true;

      // drift motes upward, recycle at the top
      const mAttr = moteGeo.attributes.position;
      for (let i = 0; i < MOTES; i++) {
        mAttr.array[i * 3 + 1] += mVel[i] * dt;
        if (mAttr.array[i * 3 + 1] > ySpan * 0.7) mAttr.array[i * 3 + 1] = -ySpan * 0.7;
      }
      mAttr.needsUpdate = true;

      pointer.x += (target.x - pointer.x) * 0.04;
      pointer.y += (target.y - pointer.y) * 0.04;
      camera.position.x = pointer.x * 1.2;
      camera.position.y = -pointer.y * 0.85;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
    };

    const animate = () => {
      if (!running) return;
      frameId = requestAnimationFrame(animate);
      renderFrame();
    };

    if (reduceMotion) {
      renderer.render(scene, camera);
    } else {
      animate();
    }

    const onVisibility = () => {
      if (document.hidden) {
        running = false;
        cancelAnimationFrame(frameId);
      } else if (!reduceMotion && !running) {
        running = true;
        clock.start();
        animate();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      running = false;
      cancelAnimationFrame(frameId);
      window.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("visibilitychange", onVisibility);
      ro.disconnect();
      disposables.forEach((d) => d.dispose());
      envRT.dispose();
      pmrem.dispose();
      envScene.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        if (o.material) o.material.dispose();
      });
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} className="three-bg" aria-hidden="true" />;
}
