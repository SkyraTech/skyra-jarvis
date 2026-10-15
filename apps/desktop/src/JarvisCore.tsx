import { useRef, useState } from 'react';
import type { View } from './App';

export default function JarvisCore({
  online,
  project,
  onOpen,
}: {
  online: boolean;
  project?: string;
  onOpen: (view: View) => void;
}) {
  const [rotation, setRotation] = useState({ x: -16, y: 24 });
  const [motion, setMotion] = useState(false);
  const drag = useRef<{ x: number; y: number; rx: number; ry: number } | null>(null);
  return (
    <section className="jarvis-stage" aria-label="Jarvis 3D operating core">
      <div className="core-copy">
        <div className="eyebrow">SKYRA INTELLIGENCE SYSTEM</div>
        <h2>
          Your world.
          <br />
          <span>In orbit.</span>
        </h2>
        <p>
          {project || 'Your workspace'} ·{' '}
          {online ? 'Connection ready' : 'Waiting for local connection'}
        </p>
        <div className="core-shortcuts">
          <button onClick={() => onOpen('Conversations')}>↗ Conversation window</button>
          <button onClick={() => onOpen('Coding runs')}>↗ Coding window</button>
          <button onClick={() => onOpen('Approvals')}>↗ Approval window</button>
        </div>
      </div>
      <div className="orb-scene">
        <div className="orb-halo" />
        <div className="orb-shadow" />
        <div
          className="orb-control"
          role="slider"
          aria-label="Rotate Jarvis core"
          aria-valuemin={-180}
          aria-valuemax={180}
          aria-valuenow={Math.round(rotation.y)}
          tabIndex={0}
          onKeyDown={(e) => {
            if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home'].includes(e.key)) {
              e.preventDefault();
              setRotation((r) =>
                e.key === 'Home'
                  ? { x: -16, y: 24 }
                  : {
                      x: Math.max(
                        -75,
                        Math.min(
                          75,
                          r.x + (e.key === 'ArrowUp' ? -8 : e.key === 'ArrowDown' ? 8 : 0),
                        ),
                      ),
                      y: Math.max(
                        -180,
                        Math.min(
                          180,
                          r.y + (e.key === 'ArrowLeft' ? -8 : e.key === 'ArrowRight' ? 8 : 0),
                        ),
                      ),
                    },
              );
            }
          }}
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId);
            drag.current = { x: e.clientX, y: e.clientY, rx: rotation.x, ry: rotation.y };
          }}
          onPointerMove={(e) => {
            if (drag.current)
              setRotation({
                x: Math.max(
                  -75,
                  Math.min(75, drag.current.rx - (e.clientY - drag.current.y) * 0.4),
                ),
                y: Math.max(
                  -180,
                  Math.min(180, drag.current.ry + (e.clientX - drag.current.x) * 0.4),
                ),
              });
          }}
          onPointerUp={() => {
            drag.current = null;
          }}
          onPointerCancel={() => {
            drag.current = null;
          }}
        >
          <div
            className="orb-tilt"
            style={{ transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)` }}
          >
            <div className={`orb-body ${motion ? 'orbiting' : ''}`}>
              {Array.from({ length: 12 }, (_, i) => (
                <i
                  className="orb-meridian"
                  key={i}
                  style={{ transform: `rotateY(${i * 15}deg)` }}
                />
              ))}
              {[-60, -30, 0, 30, 60].map((a) => (
                <i
                  className="orb-latitude"
                  key={a}
                  style={{
                    width: `${Math.cos((a * Math.PI) / 180) * 100}%`,
                    height: `${Math.cos((a * Math.PI) / 180) * 100}%`,
                    transform: `translate(-50%,-50%) rotateX(90deg) translateZ(calc(var(--orb-size, 270px) * ${Math.sin((a * Math.PI) / 180) / 2}))`,
                  }}
                />
              ))}
              <div className="orb-nucleus">
                J<span>ARVIS</span>
              </div>
              <i className="orb-equator" />
            </div>
          </div>
        </div>
        <div className="orb-caption">
          <span className={`tiny-dot ${online ? '' : 'offline'}`} />{' '}
          {online ? 'CONNECTED' : 'OFFLINE'} <span>· DRAG TO ROTATE</span>
        </div>
      </div>
      <div className="core-controls">
        <button onClick={() => onOpen('Jarvis core')}>↗ Core window</button>
        <button aria-pressed={motion} onClick={() => setMotion(!motion)}>
          {motion ? 'Pause orbit' : 'Animate orbit'}
        </button>
      </div>
    </section>
  );
}
