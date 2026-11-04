import { useEffect, useId, useRef, useState } from 'react';
import useMotionVisibility from './useMotionVisibility';
import ParticleOrb, { activityFormation } from './ParticleOrb';
import { clampOrbPosition, type Formation } from './particleGeometry';
import type { View } from './App';
import type { CoreActivity } from './coreActivity';

export default function JarvisCore({
  online,
  project,
  onOpen,
  activity,
  active,
}: {
  online: boolean;
  project?: string;
  onOpen: (view: View) => void;
  activity: CoreActivity;
  active: boolean;
}) {
  const helpId = useId();
  const [motion, setMotion] = useState(true);
  const [form, setForm] = useState<Formation | 'auto'>('auto');
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const scene = useRef<HTMLDivElement>(null);
  const control = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const visible = useMotionVisibility(active);
  const formation = form === 'auto' ? activityFormation(activity.state) : form;
  const fit = (x: number, y: number) =>
    clampOrbPosition(
      x,
      y,
      scene.current?.clientWidth || 0,
      scene.current?.clientHeight || 0,
      control.current?.clientWidth || 320,
    );
  useEffect(() => {
    if (!scene.current) return;
    const observer = new ResizeObserver(() => setPosition((old) => fit(old.x, old.y)));
    observer.observe(scene.current);
    return () => observer.disconnect();
  }, []);
  return (
    <section
      className="jarvis-stage jarvis-particle-stage"
      aria-label="Jarvis 3D operating core"
      data-activity={activity.state}
      data-animate={motion && visible && active}
    >
      <header className="particle-header">
        <div>
          <span className="eyebrow">SKYRA / INTELLIGENCE</span>
          <h2>
            JARVIS<span>01</span>
          </h2>
        </div>
        <span className="particle-connection">
          <i className={`tiny-dot ${online ? '' : 'offline'}`} />
          {online ? 'CORE CONNECTED' : 'CORE OFFLINE'}
        </span>
      </header>
      <div className="particle-scene" ref={scene}>
        <div className="particle-grid" aria-hidden="true" />
        <div className="particle-orbit-label" aria-hidden="true">
          INTENT · REASON · DELEGATE
        </div>
        <div
          className="particle-control"
          ref={control}
          role="button"
          tabIndex={0}
          aria-label="Move Jarvis orb"
          aria-describedby={helpId}
          style={{ transform: `translate(${position.x}px, ${position.y}px)` }}
          onKeyDown={(event) => {
            const delta = event.shiftKey ? 40 : 16;
            if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home'].includes(event.key)) {
              event.preventDefault();
              setPosition((old) =>
                event.key === 'Home'
                  ? { x: 0, y: 0 }
                  : fit(
                      old.x +
                        (event.key === 'ArrowLeft'
                          ? -delta
                          : event.key === 'ArrowRight'
                            ? delta
                            : 0),
                      old.y +
                        (event.key === 'ArrowUp' ? -delta : event.key === 'ArrowDown' ? delta : 0),
                    ),
              );
            }
          }}
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture(event.pointerId);
            drag.current = { x: event.clientX, y: event.clientY, px: position.x, py: position.y };
          }}
          onPointerMove={(event) => {
            if (drag.current)
              setPosition(
                fit(
                  drag.current.px + event.clientX - drag.current.x,
                  drag.current.py + event.clientY - drag.current.y,
                ),
              );
          }}
          onPointerUp={() => {
            drag.current = null;
          }}
          onPointerCancel={() => {
            drag.current = null;
          }}
          onLostPointerCapture={() => {
            drag.current = null;
          }}
        >
          <ParticleOrb
            state={activity.state}
            animate={motion && visible && active}
            formation={formation}
            rotation={24}
          />
        </div>
        <span className="particle-state-tag">
          {activity.state.toUpperCase()} / {formation.toUpperCase()}
        </span>
      </div>
      <div className="particle-console">
        <div className="core-activity" aria-live="polite" aria-atomic="true">
          <strong>{activity.label}</strong>
          <span>{activity.detail}</span>
        </div>
        <p>
          {project || 'Your workspace'} · Active project only · Recorded state · Voice not connected
        </p>
        {activity.observedAt !== undefined && (
          <time dateTime={new Date(activity.observedAt * 1000).toISOString()}>
            Observed {new Date(activity.observedAt * 1000).toLocaleTimeString()}
          </time>
        )}
      </div>
      <div className="particle-toolbar">
        <div>
          <button onClick={() => onOpen('Conversations')}>Conversation ↗</button>
          <button onClick={() => onOpen('System map')}>Systems ↗</button>
          <button onClick={() => onOpen('Approvals')}>Approvals ↗</button>
        </div>
        <div>
          <label>
            Orb form
            <select
              aria-label="Orb form"
              value={form}
              onChange={(event) => setForm(event.target.value as Formation | 'auto')}
            >
              <option value="auto">Activity driven</option>
              <option value="sphere">Sphere</option>
              <option value="torus">Orbit</option>
              <option value="wave">Wave</option>
            </select>
          </label>
          <button aria-pressed={motion} onClick={() => setMotion(!motion)}>
            {motion ? 'Pause orbit' : 'Animate orbit'}
          </button>
          <button onClick={() => setPosition({ x: 0, y: 0 })}>Center orb</button>
        </div>
      </div>
      <p className="particle-help" id={helpId}>
        Drag the orb to move · Arrow keys to position · Home to center
      </p>
    </section>
  );
}
