export type Formation = 'sphere' | 'torus' | 'wave';
export type Point3 = { x: number; y: number; z: number };

/** Deterministic point correspondence permits continuous transitions between forms. */
export function particlePoint(index: number, count: number, form: Formation, time: number): Point3 {
  const u = (index + 0.5) / count;
  const angle = index * Math.PI * (3 - Math.sqrt(5));
  const y = 1 - 2 * u;
  const radius = Math.sqrt(Math.max(0, 1 - y * y));
  if (form === 'torus') {
    const minor = u * Math.PI * 18;
    const ring = 0.72 + 0.25 * Math.cos(minor);
    return { x: ring * Math.cos(angle), y: 0.25 * Math.sin(minor), z: ring * Math.sin(angle) };
  }
  if (form === 'wave') {
    const x = Math.cos(angle) * Math.sqrt(u);
    const z = Math.sin(angle) * Math.sqrt(u);
    return { x, y: Math.sin(x * 5 + time) * Math.cos(z * 4 - time * 0.6) * 0.32, z };
  }
  const ripple = 1 + Math.sin(angle * 2 + time * 1.4) * 0.025;
  return {
    x: Math.cos(angle) * radius * ripple,
    y: y * ripple,
    z: Math.sin(angle) * radius * ripple,
  };
}

export function clampOrbPosition(
  x: number,
  y: number,
  width: number,
  height: number,
  size: number,
) {
  const limitX = Math.max(0, (width - size) / 2 - 12);
  const limitY = Math.max(0, (height - size) / 2 - 12);
  return { x: Math.max(-limitX, Math.min(limitX, x)), y: Math.max(-limitY, Math.min(limitY, y)) };
}
