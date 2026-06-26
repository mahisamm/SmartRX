import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Animated 3D backdrop for the auth screen.
 * Renders a slowly rotating DNA double-helix made of coral/amber/cream
 * spheres with connecting rungs, plus a drifting particle field.
 * Transparent canvas — the CSS gradient behind it shows through.
 *
 * Fully self-cleaning: disposes geometries/materials/renderer on unmount,
 * pauses when the tab is hidden, and honours prefers-reduced-motion.
 */
export default function ThreeBackground() {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    // ---- renderer (guard against missing WebGL) ----
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      return undefined; // no WebGL → CSS gradient remains, no crash
    }

    let width = mount.clientWidth || window.innerWidth;
    let height = mount.clientHeight || window.innerHeight;

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0); // transparent
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xfdf3e3, 0.05);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 17);

    // ---- lights ----
    scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    const key = new THREE.PointLight(0xfb7185, 1.5, 80);
    key.position.set(10, 12, 14);
    scene.add(key);
    const fill = new THREE.PointLight(0xf59e0b, 1.1, 80);
    fill.position.set(-12, -8, 10);
    scene.add(fill);

    // ---- DNA double helix ----
    const helix = new THREE.Group();
    scene.add(helix);

    const PAIRS = 26;
    const RADIUS = 3.1;
    const TURN = 0.46; // radians between pairs
    const STEP = 0.78; // vertical gap between pairs
    const ySpan = (PAIRS - 1) * STEP;

    const coral = new THREE.Color(0xfb7185);
    const amber = new THREE.Color(0xf59e0b);
    const cream = new THREE.Color(0xfff7ec);

    // shared geometries (disposed once at the end)
    const nodeGeo = new THREE.SphereGeometry(0.42, 24, 24);
    const rungGeo = new THREE.CylinderGeometry(0.07, 0.07, 1, 10);
    const Y_AXIS = new THREE.Vector3(0, 1, 0);
    const tmpDir = new THREE.Vector3();
    const tmpQuat = new THREE.Quaternion();
    const disposables = [nodeGeo, rungGeo];

    const mkNodeMat = (c) => {
      const m = new THREE.MeshStandardMaterial({
        color: c,
        roughness: 0.32,
        metalness: 0.15,
        emissive: c.clone().multiplyScalar(0.25),
      });
      disposables.push(m);
      return m;
    };
    const coralMat = mkNodeMat(coral);
    const amberMat = mkNodeMat(amber);
    const rungMat = new THREE.MeshStandardMaterial({
      color: cream,
      roughness: 0.6,
      metalness: 0.05,
      transparent: true,
      opacity: 0.55,
    });
    disposables.push(rungMat);

    for (let i = 0; i < PAIRS; i++) {
      const angle = i * TURN;
      const y = i * STEP - ySpan / 2;

      const ax = Math.cos(angle) * RADIUS;
      const az = Math.sin(angle) * RADIUS;
      const bx = Math.cos(angle + Math.PI) * RADIUS;
      const bz = Math.sin(angle + Math.PI) * RADIUS;

      const a = new THREE.Mesh(nodeGeo, i % 2 ? coralMat : amberMat);
      a.position.set(ax, y, az);
      const b = new THREE.Mesh(nodeGeo, i % 2 ? amberMat : coralMat);
      b.position.set(bx, y, bz);
      helix.add(a, b);

      // rung between the paired nodes
      const rung = new THREE.Mesh(rungGeo, rungMat);
      rung.position.set((ax + bx) / 2, y, (az + bz) / 2);
      tmpDir.set(bx - ax, 0, bz - az);
      const len = tmpDir.length();
      rung.scale.set(1, len, 1);
      tmpQuat.setFromUnitVectors(Y_AXIS, tmpDir.normalize());
      rung.quaternion.copy(tmpQuat);
      helix.add(rung);
    }

    helix.rotation.z = 0.18;

    // ---- drifting particle field ----
    const COUNT = 220;
    const positions = new Float32Array(COUNT * 3);
    for (let i = 0; i < COUNT; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 34;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 30;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 22 - 4;
    }
    const partGeo = new THREE.BufferGeometry();
    partGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const partMat = new THREE.PointsMaterial({
      color: 0xfb7185,
      size: 0.14,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
    });
    const particles = new THREE.Points(partGeo, partMat);
    scene.add(particles);
    disposables.push(partGeo, partMat);

    // ---- pointer parallax ----
    const pointer = { x: 0, y: 0 };
    const target = { x: 0, y: 0 };
    const onPointerMove = (e) => {
      target.x = (e.clientX / window.innerWidth - 0.5) * 2;
      target.y = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("pointermove", onPointerMove);

    // ---- resize ----
    const resize = () => {
      width = mount.clientWidth || window.innerWidth;
      height = mount.clientHeight || window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    const ro = new ResizeObserver(resize);
    ro.observe(mount);

    // ---- animation loop ----
    const clock = new THREE.Clock();
    let frameId = 0;
    let running = true;

    const renderFrame = () => {
      const t = clock.getElapsedTime();
      helix.rotation.y = t * 0.32;
      helix.position.y = Math.sin(t * 0.5) * 0.35;
      particles.rotation.y = t * 0.04;

      pointer.x += (target.x - pointer.x) * 0.04;
      pointer.y += (target.y - pointer.y) * 0.04;
      camera.position.x = pointer.x * 1.6;
      camera.position.y = -pointer.y * 1.1;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
    };

    const animate = () => {
      if (!running) return;
      frameId = requestAnimationFrame(animate);
      renderFrame();
    };

    if (reduceMotion) {
      renderer.render(scene, camera); // single static frame
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

    // ---- cleanup ----
    return () => {
      running = false;
      cancelAnimationFrame(frameId);
      window.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("visibilitychange", onVisibility);
      ro.disconnect();
      disposables.forEach((d) => d.dispose());
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={mountRef} className="three-bg" aria-hidden="true" />;
}
