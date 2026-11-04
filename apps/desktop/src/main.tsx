import { initializeTheme } from './ThemeControl';
import React from 'react';
import { createRoot } from 'react-dom/client';
import Workspace from './Workspace';
import '@xyflow/react/dist/style.css';
import './styles.css';
import './branding.css';

initializeTheme();
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Workspace />
  </React.StrictMode>,
);
