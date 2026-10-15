import { useEffect, useRef, useState } from 'react';
import { invoke, isTauri } from '@tauri-apps/api/core';
import App, { views, type View } from './App';

type Tab = { id: string; view: View; project: string; minimized: boolean };
const params = new URLSearchParams(location.search);
const storageKey = `jarvis.workspace.v1.${params.get('workspace') || 'main'}`;
const initialView =
  views.find((v) => v.name.toLowerCase().replaceAll(' ', '-') === params.get('panel'))?.name ||
  'Overview';
const makeTab = (view: View, project = ''): Tab => ({
  id: crypto.randomUUID(),
  view,
  project,
  minimized: false,
});
function loadTabs(): { tabs: Tab[]; active: string } {
  try {
    const data = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (
      data?.version === 1 &&
      Array.isArray(data.tabs) &&
      data.tabs.length > 0 &&
      data.tabs.length <= 8 &&
      data.tabs.every(
        (t: Tab) =>
          typeof t.id === 'string' &&
          /^[a-f0-9-]{36}$/.test(t.id) &&
          views.some((v) => v.name === t.view) &&
          typeof t.project === 'string' &&
          /^[a-zA-Z0-9_-]{0,64}$/.test(t.project) &&
          typeof t.minimized === 'boolean',
      ) &&
      new Set(data.tabs.map((t: Tab) => t.id)).size === data.tabs.length
    ) {
      const active =
        data.tabs.find((t: Tab) => t.id === data.active && !t.minimized) ||
        data.tabs.find((t: Tab) => !t.minimized);
      if (active) return { tabs: data.tabs, active: active.id };
    }
  } catch {
    /* Corrupt UI preferences never block the application. */
  }
  const tab = makeTab(initialView, params.get('project') || '');
  return { tabs: [tab], active: tab.id };
}
export default function Workspace() {
  const [layout, setLayout] = useState(loadTabs);
  const visited = useRef(new Set([layout.active]));
  visited.current.add(layout.active);
  const [newView, setNewView] = useState<View>('Overview');
  const [notice, setNotice] = useState('');
  const [focus, setFocus] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [width, setWidth] = useState(1200),
    [height, setHeight] = useState(800);
  const native = isTauri();
  const current = layout.tabs.find((t) => t.id === layout.active)!;
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({ version: 1, ...layout }));
    } catch {
      setNotice('Workspace preferences could not be saved on this device.');
    }
  }, [layout]);
  function update(id: string, patch: Partial<Tab>) {
    setLayout((old) => {
      if (
        old.tabs.every(
          (t) => t.id !== id || Object.entries(patch).every(([k, v]) => t[k as keyof Tab] === v),
        )
      )
        return old;
      return { ...old, tabs: old.tabs.map((t) => (t.id === id ? { ...t, ...patch } : t)) };
    });
  }
  function add(view: View) {
    if (layout.tabs.length >= 8) {
      setNotice('Eight tabs are open. Close a tab before opening another.');
      return;
    }
    const tab = makeTab(view, current?.project);
    setLayout((old) => ({ tabs: [...old.tabs, tab], active: tab.id }));
  }
  function remove(id: string, minimize = false) {
    setLayout((old) => {
      let tabs = minimize
        ? old.tabs.map((t) => (t.id === id ? { ...t, minimized: true } : t))
        : old.tabs.filter((t) => t.id !== id);
      let active = old.active;
      if (id === active) {
        const next = tabs.find((t) => !t.minimized);
        if (next) active = next.id;
        else if (tabs.length < 8) {
          const tab = makeTab('Overview');
          tabs = [...tabs, tab];
          active = tab.id;
        } else return old;
      }
      return { tabs, active };
    });
  }
  function move(id: string, target: string) {
    setLayout((old) => {
      const tabs = [...old.tabs];
      const from = tabs.findIndex((t) => t.id === id),
        to = tabs.findIndex((t) => t.id === target);
      if (from < 0 || to < 0) return old;
      const [tab] = tabs.splice(from, 1);
      tabs.splice(to, 0, tab);
      return { ...old, tabs };
    });
  }
  async function command(action: string, extra: Record<string, unknown> = {}) {
    if (!native) {
      setNotice('Native window controls are available in the Jarvis Windows application.');
      return;
    }
    try {
      await invoke('workspace_action', { action, ...extra });
      setNotice(
        action === 'save'
          ? 'Window arrangement saved. Use Restore arrangement to reopen it.'
          : action === 'restore'
            ? 'Saved window arrangement restored.'
            : '',
      );
      if (action === 'fullscreen') setFullscreen((v) => !v);
      if (action === 'resize' || action === 'restore') setFullscreen(false);
    } catch (error) {
      if (error === 'Restore minimized/fullscreen windows before saving arrangement') {
        setNotice(error);
        return;
      }
      setNotice(
        'Window action could not be completed. A maximum of eight separate panels is supported; check that a saved arrangement exists.',
      );
    }
  }
  async function popout(view: View, project: string) {
    if (!native) {
      setNotice('Open the Jarvis Windows application to place panels on separate monitors.');
      return;
    }
    try {
      await invoke('open_panel', { view, project: project || null });
      setNotice(
        `${view} opened in a separate window. Use its title bar to resize or move it to another monitor.`,
      );
    } catch {
      setNotice('Unable to open another panel. Close an unused panel if eight are already open.');
    }
  }
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (native && event.key === 'F11') {
        event.preventDefault();
        void command('fullscreen');
      }
      if (event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === 't') {
        event.preventDefault();
        add('Overview');
      }
      if (event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === 'w') {
        event.preventDefault();
        remove(layout.active);
      }
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  });
  return (
    <div className={`workspace-shell ${focus ? 'focus-layout' : ''}`}>
      <div
        className="workspace-bar"
        onClick={(event) => {
          const target = event.target as HTMLElement;
          const menu = target.closest('.workspace-popover button')?.closest('details');
          if (menu) menu.removeAttribute('open');
        }}
      >
        <div className="workspace-tabs" role="tablist" aria-label="Jarvis workspace tabs">
          {layout.tabs
            .filter((t) => !t.minimized)
            .map((tab) => (
              <div
                key={tab.id}
                className={`workspace-tab ${tab.id === layout.active ? 'selected' : ''}`}
                draggable
                onDragStart={(e) => e.dataTransfer.setData('text/plain', tab.id)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  move(e.dataTransfer.getData('text/plain'), tab.id);
                }}
              >
                <button
                  role="tab"
                  id={`tab-${tab.id}`}
                  tabIndex={tab.id === layout.active ? 0 : -1}
                  onKeyDown={(event) => {
                    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
                    event.preventDefault();
                    const visible = layout.tabs.filter((t) => !t.minimized);
                    const index = visible.findIndex((t) => t.id === tab.id);
                    const next =
                      visible[
                        event.key === 'Home'
                          ? 0
                          : event.key === 'End'
                            ? visible.length - 1
                            : (index + (event.key === 'ArrowLeft' ? -1 : 1) + visible.length) %
                              visible.length
                      ];
                    setLayout((old) => ({ ...old, active: next.id }));
                    document.getElementById(`tab-${next.id}`)?.focus();
                  }}
                  aria-selected={tab.id === layout.active}
                  aria-controls={`pane-${tab.id}`}
                  onClick={() => setLayout((old) => ({ ...old, active: tab.id }))}
                >
                  {tab.view}
                </button>
                <button
                  aria-label={`Close ${tab.view} tab`}
                  title="Close tab; server tasks continue"
                  onClick={() => remove(tab.id)}
                >
                  ×
                </button>
              </div>
            ))}
        </div>
        <details className="workspace-menu">
          <summary aria-label="New workspace tab">＋ Tab</summary>
          <div className="workspace-popover">
            <label>
              New tab content
              <select
                aria-label="New tab content"
                value={newView}
                onChange={(e) => setNewView(e.target.value as View)}
              >
                {views.map((v) => (
                  <option key={v.name}>{v.name}</option>
                ))}
              </select>
            </label>
            <button onClick={() => add(newView)}>Open tab</button>
            <small>Ctrl+T opens Overview. Drag tabs to reorder.</small>
          </div>
        </details>
        <details className="workspace-menu">
          <summary aria-label="Workspace arrangement">Arrange ▾</summary>
          <div className="workspace-popover">
            <button onClick={() => remove(current.id, true)}>Minimize tab</button>
            <button
              onClick={() => {
                const index = layout.tabs.findIndex((t) => t.id === current.id);
                if (index > 0) move(current.id, layout.tabs[index - 1].id);
              }}
            >
              Move tab left
            </button>
            <button onClick={() => void popout(current.view, current.project)}>
              Open tab in new window
            </button>
            <button onClick={() => void command('show_all')}>Show all windows</button>
            <button onClick={() => void command('save')}>Save window arrangement</button>
            <button onClick={() => void command('restore')}>Restore window arrangement</button>
            <label>
              Window width
              <input
                aria-label="Window width"
                type="number"
                min={640}
                max={7680}
                value={width}
                onChange={(e) => setWidth(Number(e.target.value))}
              />
            </label>
            <label>
              Window height
              <input
                aria-label="Window height"
                type="number"
                min={480}
                max={4320}
                value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
              />
            </label>
            <button onClick={() => void command('resize', { width, height })}>
              Apply window size
            </button>
            <small>
              Native windows can be dragged across monitors and resized from every edge. Window
              arrangements contain UI layout only.
            </small>
          </div>
        </details>
        <button
          className="focus-toggle"
          aria-label="Toggle focus layout"
          aria-pressed={focus}
          onClick={() => setFocus(!focus)}
        >
          ◧
        </button>
        <div className="workspace-window-controls">
          <button aria-label="Minimize window" onClick={() => void command('minimize')}>
            ─
          </button>
          <button aria-label="Maximize or restore window" onClick={() => void command('maximize')}>
            □
          </button>
          <button
            aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            onClick={() => void command('fullscreen')}
          >
            {fullscreen ? '↙' : '⛶'}
          </button>
        </div>
      </div>
      {notice && (
        <div className="workspace-notice" role="status">
          {notice}
          <button aria-label="Dismiss workspace message" onClick={() => setNotice('')}>
            ×
          </button>
        </div>
      )}
      <div className="workspace-panes">
        {layout.tabs.map((tab) => (
          <div
            key={tab.id}
            role="tabpanel"
            aria-labelledby={`tab-${tab.id}`}
            id={`pane-${tab.id}`}
            className="workspace-pane"
            hidden={tab.id !== layout.active}
          >
            <App
              view={tab.view}
              setView={(view) => update(tab.id, { view })}
              initialProject={tab.project}
              active={tab.id === layout.active}
              onProjectChange={(project) => update(tab.id, { project })}
              onPopout={(view, project) => void popout(view, project)}
            />
          </div>
        ))}
      </div>
      {layout.tabs.some((t) => t.minimized) && (
        <div className="minimized-tabs" aria-label="Minimized tabs">
          {layout.tabs
            .filter((t) => t.minimized)
            .map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  update(tab.id, { minimized: false });
                  setLayout((old) => ({ ...old, active: tab.id }));
                }}
              >
                Restore {tab.view}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
