/** Native WebView2 acceptance; generated fixture only. Debug port is test-only and loopback. */
import { chromium, expect } from '@playwright/test';
import { spawn, spawnSync } from 'node:child_process';
import { readFile, writeFile, stat } from 'node:fs/promises';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const desktop = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repo = path.resolve(desktop, '../..');
const python = path.join(repo, 'venv/Scripts/python.exe');
const executable =
  process.env.JARVIS_TEST_EXE || path.join(desktop, 'src-tauri/target/release/jarvis-desktop.exe');
const root = path.join(repo, '.runtime', `desktop-native-${Date.now()}`);
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function port() {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const value = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  return value;
}
const corePort = await port(),
  debugPort = await port();
const seeded = spawnSync(
  python,
  [path.join(desktop, 'tests/native_fixture.py'), '--directory', root, '--port', String(corePort)],
  { encoding: 'utf8', windowsHide: true },
);
if (seeded.status !== 0) throw new Error(`Unable to prepare native fixture: ${seeded.stderr}`);
const fixture = JSON.parse(seeded.stdout);
const config = JSON.parse(await readFile(path.join(root, 'launcher.json'), 'utf8'));
const core = spawn(
  python,
  [
    path.join(desktop, 'tests/native_core.py'),
    '--auth-config',
    config.auth_config,
    '--database',
    config.database,
    '--workspace-config',
    config.workspace_config,
    '--runtime-config',
    config.runtime_config,
    '--port',
    String(corePort),
  ],
  {
    windowsHide: true,
    stdio: 'pipe',
    env: { ...process.env, JARVIS_NATIVE_TEST_KEY: 'fixture-not-a-real-api-key' },
  },
);
let app, browser, second;
try {
  let ready = false;
  for (let i = 0; i < 120; i++) {
    if (core.exitCode !== null) throw new Error('Fixture core exited before becoming ready');
    try {
      const response = await fetch(`http://127.0.0.1:${corePort}/v1/health`, {
        signal: AbortSignal.timeout(1000),
      });
      if (response.status === 401) {
        ready = true;
        break;
      }
    } catch {
      /* waiting for loopback core */
    }
    await pause(250);
  }
  if (!ready) throw new Error('Fixture core did not become ready');
  app = spawn(executable, [], {
    windowsHide: false,
    stdio: 'pipe',
    env: {
      ...process.env,
      JARVIS_DESKTOP_CONFIG: path.join(root, 'desktop.json'),
      JARVIS_EXPORT_ROOT: path.join(root, 'exports'),
      WEBVIEW2_USER_DATA_FOLDER: path.join(root, 'webview-profile'),
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-address=127.0.0.1 --remote-debugging-port=${debugPort}`,
    },
  });
  let endpoint;
  for (let i = 0; i < 120; i++) {
    if (app.exitCode !== null) throw new Error('Native application exited before attaching');
    try {
      endpoint = await (await fetch(`http://127.0.0.1:${debugPort}/json/version`)).json();
      if (endpoint.webSocketDebuggerUrl) break;
    } catch {
      /* wait for WebView2 */
    }
    await pause(500);
  }
  if (!endpoint?.webSocketDebuggerUrl)
    throw new Error('Native WebView2 debug connection was unavailable');
  browser = await chromium.connectOverCDP(endpoint.webSocketDebuggerUrl);
  const context = browser.contexts()[0];
  let page;
  for (let i = 0; i < 40; i++) {
    page = context.pages().find((p) => p.url().includes('tauri.localhost'));
    if (page) break;
    await pause(250);
  }
  if (!page) throw new Error('Native Jarvis page was not found');
  await expect(page.getByText('Local core connected')).toBeVisible({ timeout: 30000 });
  await expect(page.getByText('VISUAL PREVIEW', { exact: false })).toHaveCount(0);
  const builtHtml = await readFile(path.join(desktop, 'dist/index.html'), 'utf8');
  const expectedAsset = builtHtml.match(/src="([^"]+\.js)"/)?.[1];
  if (!expectedAsset) throw new Error('Built frontend asset was not found');
  await expect(page.locator(`script[src$="/${path.posix.basename(expectedAsset)}"]`)).toHaveCount(
    1,
  );
  await expect(page.getByRole('button', { name: 'Edit project permissions' })).toBeEnabled();
  await page.getByRole('button', { name: 'Edit project permissions' }).click();
  await expect(page.getByRole('combobox', { name: 'Permission mode', exact: true })).toHaveValue(
    'ask',
  );
  await page.getByRole('button', { name: 'Save permission policy' }).click();
  await expect(page.getByRole('status')).toContainText('Permission policy updated');
  await page.screenshot({ path: path.join(root, 'native-overview.png'), fullPage: true });
  await page.getByRole('button', { name: '◇ Repair proposals' }).click();
  await page
    .getByRole('button', { name: /workspace:fixture native-acceptance-fixture ready/ })
    .click();
  await page.getByRole('button', { name: 'Accept into coding run' }).click();
  await expect(page.getByRole('status')).toContainText('Proposal accepted');
  for (let step = 0; step < 3; step++) {
    await page.getByRole('button', { name: '⌁ Coding runs' }).click();
    await page.getByRole('button', { name: /workspace:fixture Step/ }).click();
    await page.getByRole('button', { name: 'Advance one step' }).click();
    await expect(page.locator('.detail .panel-heading')).toContainText('waiting approval', {
      timeout: 30000,
    });
    await page.getByRole('button', { name: /✓Approvals|✓ Approvals/ }).click();
    await page.getByRole('button', { name: /workspace:fixture Review exact action/ }).click();
    await page.getByRole('button', { name: 'Approve exact action' }).click();
    await expect(page.getByRole('status')).toContainText('Decision saved');
    await page.getByRole('button', { name: '⌁ Coding runs' }).click();
    await page.getByRole('button', { name: /workspace:fixture Step/ }).click();
    await page.getByRole('button', { name: 'Advance one step' }).click();
    await expect(page.locator('.detail .panel-heading')).toContainText('planned', {
      timeout: 30000,
    });
  }
  await page.getByRole('button', { name: 'Advance one step' }).click();
  await expect(page.locator('.detail .panel-heading')).toContainText('ready for review', {
    timeout: 30000,
  });
  await expect(page.locator('.evidence')).toHaveCount(4);
  await page.locator('.evidence').last().click();
  await expect(page.locator('.evidence-output')).toContainText('return 42');
  await page.screenshot({ path: path.join(root, 'native-review.png'), fullPage: true });
  const sourcePreserved = (await readFile(path.join(root, 'source/app.py'), 'utf8')).includes(
    'return 41',
  );
  if (!sourcePreserved) throw new Error('Original source was modified');
  if (!(await readFile(path.join(root, 'snapshot/files/feature.py'), 'utf8')).includes('return 42'))
    throw new Error('New module missing from snapshot');
  await expect(page.locator('.evidence-output')).toContainText('/dev/null');
  try {
    await stat(path.join(root, 'source/feature.py'));
    throw new Error('Original project gained a generated file');
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }

  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: '＋ New', exact: true }).click();
  await page
    .getByLabel('Message', { exact: true })
    .fill('Native persisted conversation acceptance.');
  await page.getByRole('button', { name: 'Save message', exact: true }).click();
  await expect(
    page.getByText('Native persisted conversation acceptance.', { exact: true }),
  ).toBeVisible();
  await page.getByLabel('Response mode').selectOption('chat');
  await page.getByLabel('Online model').selectOption('fixture');
  await page.getByLabel('Message', { exact: true }).fill('Give a concise fixture reply.');
  await page.getByRole('button', { name: 'Send to model', exact: true }).click();
  await expect(page.locator('.model-reply')).toHaveText(
    'Native fixture response, stored successfully.',
  );
  await expect(page.locator('.usage')).toContainText('total tokens: 37');
  await page.getByLabel('Response mode').selectOption('plan');
  await page.getByLabel('Message', { exact: true }).fill('Plan the fixture client website.');
  await page.getByRole('button', { name: 'Generate draft plan', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Native client website plan' })).toBeVisible();
  await expect(page.locator('.project-plan')).toContainText('Acceptance criteria');
  await page.screenshot({ path: path.join(root, 'native-plan.png'), fullPage: true });
  await page.getByRole('button', { name: 'Save specification version', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Specification version 1 - draft', exact: true }),
  ).toBeVisible();
  await page.getByText('01_PRODUCT_REQUIREMENTS.md', { exact: true }).click();
  await expect(
    page.locator('pre').filter({ hasText: '# Native client website plan' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Approve reviewed specification', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Specification version 1 - approved', exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: path.join(root, 'native-specification.png'), fullPage: true });
  await page.getByRole('button', { name: 'Edit as new revision', exact: true }).click();
  const revision = page.getByRole('dialog');
  await revision
    .getByLabel('Additional specification document', { exact: true })
    .selectOption('02_SYSTEM_ARCHITECTURE.md');
  await revision.getByRole('button', { name: 'Add document', exact: true }).click();
  await revision
    .getByLabel('Document content', { exact: true })
    .fill('# Native architecture\nOwner reviewed Windows fixture.');
  await revision.getByRole('button', { name: 'Save revised draft', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Specification version 2 - draft', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Export approved documents', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Approve reviewed specification', exact: true }).click();
  await page.getByRole('button', { name: 'Export approved documents', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Exported 5 documents:');
  const exportedDirectory = (await page.getByRole('status').innerText()).split(
    'Exported 5 documents: ',
  )[1];
  if (
    !exportedDirectory ||
    !path.resolve(exportedDirectory).startsWith(path.resolve(root, 'exports') + path.sep)
  )
    throw new Error('Export escaped isolated fixture');
  const manifest = JSON.parse(
    await readFile(path.join(exportedDirectory, 'manifest.json'), 'utf8'),
  );
  if (manifest.version !== 2 || manifest.project !== fixture.project)
    throw new Error('Export provenance mismatch');
  const exportedDocs = JSON.parse(manifest.canonical_documents);
  for (const [name, content] of Object.entries(exportedDocs)) {
    if ((await readFile(path.join(exportedDirectory, name), 'utf8')) !== content)
      throw new Error('Exported document mismatch');
  }
  await page.getByRole('button', { name: 'Export approved documents', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Verified existing export:');
  await page.screenshot({
    path: path.join(root, 'native-specification-export.png'),
    fullPage: true,
  });

  await page.getByRole('button', { name: '⚙ Setup' }).click();
  await expect(page.getByRole('heading', { name: 'Set up your workspace' })).toBeVisible();
  await expect(page.locator('.setup-panel')).toContainText('native-acceptance-fixture');
  // Real native panel lifecycle; no browser popup simulation and no paid provider calls.
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: 'Open current panel in new window', exact: true }).click();
  async function panelPage() {
    for (let i = 0; i < 80; i++) {
      const panel = browser
        .contexts()
        .flatMap((c) => c.pages())
        .find((p) => p.url().includes('panel=conversations'));
      if (panel) return panel;
      await pause(250);
    }
    throw new Error('Native conversation panel was not created');
  }
  let child = await panelPage();
  await expect(child.getByText('Local core connected', { exact: true })).toHaveCount(1, {
    timeout: 30000,
  });
  await expect(child.getByLabel('Project', { exact: true })).toHaveValue(fixture.project);
  await child.getByRole('button', { name: /Conversation / }).click();
  await expect(
    child.getByText('Native persisted conversation acceptance.', { exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: '◉ Jarvis core', exact: true }).click();
  await page.getByRole('button', { name: 'Open current panel in new window', exact: true }).click();
  await expect
    .poll(
      () =>
        browser
          .contexts()
          .flatMap((c) => c.pages())
          .filter((p) => p.url().includes('panel=')).length,
    )
    .toBe(2);
  const coreChild = browser
    .contexts()
    .flatMap((c) => c.pages())
    .find((p) => p.url().includes('panel=jarvis-core'));
  await expect(coreChild.getByRole('slider', { name: 'Rotate Jarvis core' })).toBeVisible({
    timeout: 30000,
  });
  const closeCore = spawnSync(
    python,
    [
      path.join(desktop, 'tests/window_probe.py'),
      '--pid',
      String(app.pid),
      '--title',
      'Jarvis · Jarvis core',
      '--close',
    ],
    { encoding: 'utf8', windowsHide: true, timeout: 15000 },
  );
  if (closeCore.status !== 0) throw new Error('Could not close 3D core panel');
  await expect
    .poll(
      () =>
        browser
          .contexts()
          .flatMap((c) => c.pages())
          .filter((p) => p.url().includes('panel=')).length,
    )
    .toBe(1);
  const probePanel = () => {
    const result = spawnSync(
      python,
      [
        path.join(desktop, 'tests/window_probe.py'),
        '--pid',
        String(app.pid),
        '--title',
        'Jarvis · Conversations',
      ],
      { encoding: 'utf8', windowsHide: true, timeout: 15000 },
    );
    if (result.status !== 0) throw new Error('Native panel probe failed');
    return JSON.parse(result.stdout).windows[0];
  };
  await child.getByLabel('Workspace arrangement', { exact: true }).click();
  await child.getByLabel('Window width', { exact: true }).fill('960');
  await child.getByLabel('Window height', { exact: true }).fill('700');
  await child.getByRole('button', { name: 'Apply window size', exact: true }).click();
  await expect.poll(() => child.evaluate(() => innerWidth)).toBe(960);
  await child.getByRole('button', { name: 'Maximize or restore window', exact: true }).click();
  await expect.poll(() => probePanel().maximized).toBe(true);
  await child.getByRole('button', { name: 'Maximize or restore window', exact: true }).click();
  await expect.poll(() => probePanel().maximized).toBe(false);
  await child.getByRole('button', { name: 'Enter fullscreen', exact: true }).click();
  await expect.poll(() => probePanel().caption).toBe(false);
  await child.getByRole('button', { name: 'Exit fullscreen', exact: true }).click();
  await expect.poll(() => probePanel().caption).toBe(true);
  await child.getByRole('button', { name: 'Minimize window', exact: true }).click();
  await expect.poll(() => probePanel().minimized).toBe(true);
  await page.getByLabel('Workspace arrangement', { exact: true }).click();
  await page.getByRole('button', { name: 'Show all windows', exact: true }).click();
  await expect.poll(() => probePanel().minimized).toBe(false);
  await page.getByLabel('Workspace arrangement', { exact: true }).click();
  await page.getByRole('button', { name: 'Save window arrangement', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Window arrangement saved');
  const arrangementPath = path.join(root, 'window-arrangement.json');
  const arrangement = JSON.parse(await readFile(arrangementPath, 'utf8'));
  if (arrangement.windows.length !== 2)
    throw new Error('Expected main and independent native panel in arrangement');
  const saved = arrangement.windows.find((w) => w.label !== 'main');
  saved.bounds.x = 999999;
  saved.bounds.y = 999999;
  await writeFile(arrangementPath, JSON.stringify(arrangement));
  const closePanel = () =>
    spawnSync(
      python,
      [
        path.join(desktop, 'tests/window_probe.py'),
        '--pid',
        String(app.pid),
        '--title',
        'Jarvis · Conversations',
        '--close',
      ],
      { encoding: 'utf8', windowsHide: true, timeout: 15000 },
    );
  if (closePanel().status !== 0) throw new Error('Could not close independent panel');
  await expect
    .poll(
      () =>
        browser
          .contexts()
          .flatMap((c) => c.pages())
          .filter((p) => p.url().includes('panel=conversations')).length,
    )
    .toBe(0);
  await page.getByLabel('Workspace arrangement', { exact: true }).click();
  await page.getByRole('button', { name: 'Restore window arrangement', exact: true }).click();
  child = await panelPage();
  await expect(child.getByText('Local core connected', { exact: true })).toHaveCount(1, {
    timeout: 30000,
  });
  const recovered = probePanel();
  if (!recovered.visible || recovered.rect[0] > 100000 || recovered.rect[1] > 100000)
    throw new Error('Saved offscreen panel was not recovered');
  await child.screenshot({ path: path.join(root, 'native-independent-panel.png'), fullPage: true });
  closePanel();
  await page.getByRole('button', { name: '⌘ Overview' }).click();
  await page.screenshot({ path: path.join(root, 'native-3d-workspace.png'), fullPage: true });
  const bytes = await readFile(executable);
  const peOffset = bytes.readUInt32LE(0x3c);
  const windowsSubsystem = bytes.readUInt16LE(peOffset + 24 + 68);
  if (windowsSubsystem !== 2)
    throw new Error('Release executable is not a Windows GUI subsystem application');
  const hiddenResult = spawnSync(
    python,
    [path.join(desktop, 'tests/window_probe.py'), '--pid', String(app.pid), '--close'],
    { encoding: 'utf8', windowsHide: true, timeout: 15000 },
  );
  const hidden = JSON.parse(hiddenResult.stdout);
  if (!hidden.close_posted || hidden.after_visible !== 0 || !hidden.alive || core.exitCode !== null)
    throw new Error('Close-to-tray lifecycle failed: ' + JSON.stringify(hidden));
  second = spawn(executable, [], {
    windowsHide: false,
    stdio: 'pipe',
    env: {
      ...process.env,
      JARVIS_DESKTOP_CONFIG: path.join(root, 'desktop.json'),
      JARVIS_EXPORT_ROOT: path.join(root, 'exports'),
      WEBVIEW2_USER_DATA_FOLDER: path.join(root, 'webview-profile'),
    },
  });
  for (let i = 0; i < 40 && second.exitCode === null; i++) await pause(250);
  if (second.exitCode !== 0)
    throw new Error('Single-instance activation did not exit the second process');
  const restoredResult = spawnSync(
    python,
    [path.join(desktop, 'tests/window_probe.py'), '--pid', String(app.pid)],
    { encoding: 'utf8', windowsHide: true, timeout: 15000 },
  );
  const restored = JSON.parse(restoredResult.stdout);
  if (restored.after_visible < 1 || !restored.alive)
    throw new Error('Single-instance activation did not restore the original window');
  if (!(await stat(path.join(root, 'webview-profile'))).isDirectory())
    throw new Error('Isolated native WebView profile was not created');
  const summary = {
    fixture: true,
    isolated_webview_profile: true,
    live_model_calls: 0,
    project: fixture.project,
    proposal: fixture.proposal,
    native_core_connected: true,
    dpapi_credentials: true,
    permission_policy_saved: true,
    frontend_asset: expectedAsset,
    approval_gates: 3,
    run_state: 'ready_for_review',
    evidence_reports: 4,
    source_preserved: sourcePreserved,
    reviewed_new_file_created_and_tested: true,
    conversation_saved: true,
    model_chat_completed: true,
    structured_plan_completed: true,
    versioned_specification_approved: true,
    specification_revision_and_export_verified: true,
    setup_readiness_verified: true,
    independent_native_panel: true,
    simultaneous_native_panels: 2,
    panel_resize_maximize_fullscreen_minimize: true,
    window_arrangement_saved_and_restored: true,
    offscreen_window_recovered: true,
    windows_gui_subsystem: windowsSubsystem,
    close_hides_to_tray: true,
    single_instance_restores_window: true,
  };
  await writeFile(path.join(root, 'review.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify({ ...summary, artifacts: root }, null, 2));
} finally {
  if (browser) await browser.close().catch(() => {});
  if (app && app.exitCode === null) app.kill();
  if (second && second.exitCode === null) second.kill();
  if (core.exitCode === null) core.kill();
}
