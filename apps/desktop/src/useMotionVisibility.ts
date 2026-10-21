import { useEffect, useState } from 'react';
import { isTauri } from '@tauri-apps/api/core';
import { getCurrentWindow } from '@tauri-apps/api/window';

/** Native window state is authoritative; WebView document events alone miss minimization. */
export default function useMotionVisibility(active: boolean) {
  const [visible, setVisible] = useState(!isTauri() && !document.hidden);
  useEffect(() => {
    if (!active) {
      setVisible(false);
      return;
    }
    if (!isTauri()) {
      const update = () => setVisible(!document.hidden);
      update();
      document.addEventListener('visibilitychange', update);
      return () => {
        document.removeEventListener('visibilitychange', update);
      };
    }
    const nativeWindow = getCurrentWindow();
    const unlisteners: (() => void)[] = [];
    let disposed = false,
      revision = 0;
    async function sync() {
      const current = ++revision;
      try {
        const [shown, minimized] = await Promise.all([
          nativeWindow.isVisible(),
          nativeWindow.isMinimized(),
        ]);
        if (!disposed && current === revision) setVisible(shown && !minimized && !document.hidden);
      } catch {
        if (!disposed && current === revision) setVisible(false);
      }
    }
    function subscribe(pending: Promise<() => void>) {
      void pending
        .then((stop) => {
          if (disposed) stop();
          else unlisteners.push(stop);
        })
        .catch(() => {
          if (!disposed) setVisible(false);
        });
    }
    subscribe(nativeWindow.onFocusChanged(() => void sync()));
    subscribe(nativeWindow.onResized(() => void sync()));
    document.addEventListener('visibilitychange', sync);
    void sync();
    // Handles OS minimize/tray transitions even when WebView focus/visibility events are absent.
    const timer = window.setInterval(() => void sync(), 1000);
    return () => {
      disposed = true;
      revision++;
      clearInterval(timer);
      document.removeEventListener('visibilitychange', sync);
      unlisteners.forEach((stop) => stop());
    };
  }, [active]);
  return active && visible;
}
