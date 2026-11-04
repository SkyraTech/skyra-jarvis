import { useEffect, useRef, useState } from 'react';
import { particlePoint, type Formation, type Point3 } from './particleGeometry';
import type { CoreActivity } from './coreActivity';

const count = 1000;
const palette: Record<CoreActivity['state'], [number, number]> = {
  idle: [188, 270],
  thinking: [265, 185],
  planning: [265, 320],
  coding: [190, 255],
  testing: [150, 195],
  inspecting: [205, 270],
  review: [35, 315],
  stopping: [35, 10],
  blocked: [350, 295],
  paused: [215, 240],
  queued: [215, 265],
  unknown: [215, 240],
  offline: [215, 230],
};

export function activityFormation(state: CoreActivity['state']): Formation {
  return state === 'testing' || state === 'inspecting'
    ? 'torus'
    : state === 'coding' || state === 'planning' || state === 'thinking'
      ? 'wave'
      : 'sphere';
}

/** Rendering only: visuals never report a task result or grant execution authority. */
export default function ParticleOrb({
  state,
  animate,
  formation,
  rotation,
}: {
  state: CoreActivity['state'];
  animate: boolean;
  formation: Formation;
  rotation: number;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const points = useRef<Point3[]>([]);
  const clock = useRef(0);
  const [reduced, setReduced] = useState(
    () => matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  useEffect(() => {
    const media = matchMedia('(prefers-reduced-motion: reduce)');
    const change = () => setReduced(media.matches);
    media.addEventListener('change', change);
    return () => media.removeEventListener('change', change);
  }, []);
  useEffect(() => {
    const element = canvas.current;
    const ctx = element?.getContext('2d');
    if (!element || !ctx) return;
    let frame = 0,
      last = 0,
      disposed = false;
    const moving = animate && !reduced;
    const [hue, accent] = palette[state];
    function paint(timestamp: number) {
      if (disposed || !element || !ctx) return;
      const elapsed = last ? Math.min(0.1, (timestamp - last) / 1000) : 0;
      last = timestamp;
      if (moving) clock.current += elapsed;
      const time = clock.current;
      const width = element.clientWidth || 320;
      const height = element.clientHeight || 320;
      const dpr = Math.min(devicePixelRatio || 1, 2);
      if (
        element.width !== Math.round(width * dpr) ||
        element.height !== Math.round(height * dpr)
      ) {
        element.width = Math.round(width * dpr);
        element.height = Math.round(height * dpr);
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);
      const scale = Math.min(width, height) * 0.35;
      const spin = time * 0.16 + (rotation * Math.PI) / 180;
      const blend = moving ? 1 - Math.exp(-elapsed * 3) : 1;
      const projected = [];
      for (let index = 0; index < count; index++) {
        const target = particlePoint(index, count, formation, time);
        const old = points.current[index] || target;
        const point = {
          x: old.x + (target.x - old.x) * blend,
          y: old.y + (target.y - old.y) * blend,
          z: old.z + (target.z - old.z) * blend,
        };
        points.current[index] = point;
        const x = point.x * Math.cos(spin) - point.z * Math.sin(spin);
        const z = point.x * Math.sin(spin) + point.z * Math.cos(spin);
        const y = point.y * 0.88 - z * 0.34;
        projected.push({ x, y, z, index });
      }
      projected.sort((a, b) => a.z - b.z);
      const lightTheme = document.documentElement.dataset.theme === 'light';
      for (const point of projected) {
        const depth = (point.z + 1.1) / 2.2;
        const perspective = 1 + point.z * 0.12;
        const colour = point.index % 7 === 0 ? accent : hue;
        ctx.fillStyle = `hsla(${colour}, ${state === 'offline' ? 12 : 88}%, ${lightTheme ? 30 + depth * 16 : 60 + depth * 27}%, ${0.2 + depth * 0.7})`;
        ctx.beginPath();
        ctx.arc(
          width / 2 + point.x * scale * perspective,
          height / 2 + point.y * scale * perspective,
          0.65 + depth * 1.45,
          0,
          Math.PI * 2,
        );
        ctx.fill();
      }
      element.dataset.formation = formation;
      element.dataset.running = String(moving);
      if (moving) frame = requestAnimationFrame(paint);
    }
    paint(performance.now());
    const observer = new ResizeObserver(() => {
      if (!moving) paint(performance.now());
    });
    observer.observe(element);
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [state, animate, formation, reduced, rotation]);
  return <canvas ref={canvas} className="particle-orb" aria-hidden="true" />;
}
