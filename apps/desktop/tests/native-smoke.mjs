/** Native WebView2 acceptance; generated fixture only. Debug port is test-only and loopback. */
import { chromium, expect } from '@playwright/test';
import { spawn, spawnSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
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
  await page.getByRole('button', { name: '⚙ Setup' }).click();
  await expect(page.getByRole('heading', { name: 'Set up your workspace' })).toBeVisible();
  await expect(page.locator('.setup-panel')).toContainText('native-acceptance-fixture');
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
    env: { ...process.env, JARVIS_DESKTOP_CONFIG: path.join(root, 'desktop.json') },
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
  const summary = {
    fixture: true,
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
    conversation_saved: true,
    model_chat_completed: true,
    structured_plan_completed: true,
    setup_readiness_verified: true,
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
