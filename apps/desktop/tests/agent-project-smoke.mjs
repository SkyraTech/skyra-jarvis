/** Independent browser acceptance over a reviewed generated internal task-board only. */
import { chromium, expect } from '@playwright/test';
import { spawn, spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { once } from 'node:events';
import { createHash } from 'node:crypto';

const desktop = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repo = path.resolve(desktop, '../..');
const python = path.join(repo, 'venv/Scripts/python.exe');
const evaluation = process.argv[2] ? path.resolve(process.argv[2]) : null;
if (!evaluation) throw new Error('Provide the generated evaluation directory');
function admit() {
  const result = spawnSync(
    python,
    [path.join(repo, 'packages/agent-runtime/evaluate.py'), '--browser-inputs', evaluation],
    { cwd: repo, windowsHide: true, encoding: 'utf8', timeout: 15000 },
  );
  if (result.status !== 0) throw new Error('Current reviewed test evidence is required');
  return JSON.parse(result.stdout);
}
const inputs = admit();
const directory = path.join(inputs.root, `browser-${Date.now()}`);
await mkdir(directory);
const code = path.join(directory, 'code');
await mkdir(code);
for (const [name, digest] of Object.entries(inputs.input_hashes)) {
  const source = path.resolve(inputs.files, name);
  if (!source.startsWith(path.resolve(inputs.files) + path.sep))
    throw new Error('Selected relative path required');
  const content = await readFile(source);
  if (createHash('sha256').update(content).digest('hex') !== digest)
    throw new Error('Reviewed input changed before copying');
  const destination = path.join(code, name);
  await mkdir(path.dirname(destination), { recursive: true });
  await writeFile(destination, content, { flag: 'wx' });
}
const checks = [];
const external = [];
const pageErrors = [];
let server, browser, context, page, base;
async function check(name, action) {
  try {
    await action();
    checks.push({ name, passed: true });
  } catch (error) {
    checks.push({ name, passed: false, error: error.name, detail: error.message.slice(0, 800) });
  }
}
let cleanup = false;
try {
  server = spawn(
    python,
    [
      '-I',
      '-B',
      '-u',
      '-c',
      'import sys;sys.path.insert(0,sys.argv[1]);from server import serve\nwith serve(0) as s:\n print(s.server_port,flush=True);s.serve_forever()',
      code,
    ],
    { cwd: directory, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] },
  );
  const port = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Loopback server readiness timed out')), 15000);
    server.once('error', reject);
    server.once('exit', () => reject(new Error('Loopback server exited before readiness')));
    let output = '';
    server.stdout.on('data', (chunk) => {
      output += chunk.toString();
      if (/^\d+\r?\n/.test(output)) {
        clearTimeout(timer);
        resolve(Number(output.trim()));
      }
    });
  });
  base = `http://127.0.0.1:${port}`;
  browser = await chromium.launch({ channel: 'msedge', headless: true });
  context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    reducedMotion: 'reduce',
  });
  context.setDefaultTimeout(10000);
  context.setDefaultNavigationTimeout(20000);
  await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
  await context.route('**/*', (route) => {
    if (new URL(route.request().url()).origin === base) return route.continue();
    external.push(route.request().url());
    return route.abort();
  });
  page = await context.newPage();
  page.on('pageerror', (error) => pageErrors.push(error.name));
  await page.goto(base);
  await check('empty state and accessible input', async () => {
    await expect(page.getByRole('heading', { name: 'Skyra Task Board' })).toBeVisible();
    await expect(page.getByLabel('Task title', { exact: true })).toBeVisible();
    await expect(page.getByText(/No tasks/)).toBeVisible();
  });
  const title = '<img src=x onerror="window.untrustedTitle=true">';
  await check('keyboard creation renders title as text', async () => {
    await page.getByLabel('Task title', { exact: true }).fill(title);
    await page.getByLabel('Task title', { exact: true }).press('Enter');
    await expect(page.getByText(title, { exact: true })).toBeVisible();
    expect(await page.locator('img').count()).toBe(0);
    expect(await page.evaluate(() => window.untrustedTitle)).toBeUndefined();
  });
  await check('completion and reload preserve data', async () => {
    await page.getByRole('button', { name: 'Complete', exact: true }).click();
    await expect(page.getByText('Completed', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByText(title, { exact: true })).toBeVisible();
    await expect(page.getByText('Completed', { exact: true })).toBeVisible();
  });
  await page.screenshot({ path: path.join(directory, 'desktop.png'), fullPage: true });
  await check('failed creation preserves input and exposes error', async () => {
    await page.route(`${base}/api/tasks`, (route) =>
      route.request().method() === 'POST'
        ? route.fulfill({ status: 503, body: 'Unavailable' })
        : route.continue(),
    );
    await page.getByLabel('Task title', { exact: true }).fill('Keep my input');
    await page.getByRole('button', { name: 'Add task', exact: true }).click();
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByLabel('Task title', { exact: true })).toHaveValue('Keep my input');
    await expect(page.getByRole('button', { name: 'Add task', exact: true })).toBeEnabled();
    await page.unroute(`${base}/api/tasks`);
  });
  await check('duplicate submissions are suppressed', async () => {
    let posts = 0;
    await page.route(`${base}/api/tasks`, async (route) => {
      if (route.request().method() === 'POST') {
        posts++;
        await new Promise((resolve) => setTimeout(resolve, 300));
      }
      await route.continue();
    });
    await page.getByLabel('Task title', { exact: true }).fill('Single request');
    await page.locator('form').evaluate((form) => {
      form.requestSubmit();
      form.requestSubmit();
    });
    await expect(page.getByText('Single request', { exact: true })).toBeVisible();
    expect(posts).toBe(1);
    await page.unroute(`${base}/api/tasks`);
  });
  await check('mobile long-title layout stays within viewport', async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByLabel('Task title', { exact: true }).fill('W'.repeat(200));
    await page.getByRole('button', { name: 'Add task', exact: true }).click();
    await expect(page.getByText('W'.repeat(200), { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  });
  await page.screenshot({ path: path.join(directory, 'mobile.png'), fullPage: true });
  await check('wrong method on completion route is rejected as 405', async () => {
    const rows = await (
      await fetch(`${base}/api/tasks`, { signal: AbortSignal.timeout(10000) })
    ).json();
    expect(
      (
        await fetch(`${base}/api/tasks/${rows[0].id}/complete`, {
          signal: AbortSignal.timeout(10000),
        })
      ).status,
    ).toBe(405);
  });
  await check('corruption error is visible without data reset', async () => {
    await writeFile(path.join(directory, 'tasks.json'), 'null');
    await page.reload();
    await expect(page.getByRole('alert')).toBeVisible();
    expect(await readFile(path.join(directory, 'tasks.json'), 'utf8')).toBe('null');
  });
  await check('no script errors or external requests', async () => {
    expect(pageErrors).toEqual([]);
    expect(external).toEqual([]);
  });
  await check('tested source hashes remain unchanged', async () => {
    expect(admit()).toEqual(inputs);
    for (const [name, digest] of Object.entries(inputs.input_hashes)) {
      expect(
        createHash('sha256')
          .update(await readFile(path.join(code, name)))
          .digest('hex'),
      ).toBe(digest);
    }
  });
} finally {
  if (context) await context.tracing.stop({ path: path.join(directory, 'trace.zip') });
  if (browser) await browser.close();
  if (server && server.exitCode === null) {
    const exited = once(server, 'exit');
    server.kill();
    await Promise.race([
      exited,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Server cleanup timed out')), 5000),
      ),
    ]);
  }
  cleanup = !server || server.exitCode !== null || server.signalCode !== null;
  const review = {
    scope: 'internal-task-board-browser-v1',
    passed: cleanup && checks.length === 10 && checks.every((c) => c.passed),
    inputs,
    checks,
    cleanup_confirmed: cleanup,
    live_model_calls: 0,
    completed_project: false,
  };
  await writeFile(path.join(directory, 'review.json'), JSON.stringify(review, null, 2));
  console.log(JSON.stringify({ ...review, artifacts: directory }, null, 2));
  if (!review.passed) process.exitCode = 1;
}
