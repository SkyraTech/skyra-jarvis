import { useEffect, useState } from 'react';
type Theme = 'light' | 'dark';
const key = 'skyra.appearance.v1';
function preference(): Theme {
  try { const saved = localStorage.getItem(key); if (saved === 'light' || saved === 'dark') return saved; } catch {}
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
export function initializeTheme() { document.documentElement.dataset.theme = preference(); }
export default function ThemeControl() {
  const [theme, setTheme] = useState<Theme>(preference);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(key, theme); } catch {}
  }, [theme]);
  useEffect(() => {
    const sync = (event: StorageEvent) => { if (event.key === key) setTheme(preference()); };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);
  return <label className="appearance-control"><span>Appearance</span><select aria-label="Appearance" value={theme} onChange={event => setTheme(event.target.value as Theme)}><option value="light">Light</option><option value="dark">Dark</option></select></label>;
}
