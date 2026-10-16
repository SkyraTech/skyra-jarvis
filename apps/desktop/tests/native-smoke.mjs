/** Native WebView2 acceptance; generated fixture only. Debug port is test-only and loopback. */
import { chromium, expect } from '@playwright/test';
import { spawn, spawnSync } from 'node:child_process';
import { readFile, writeFile, stat, unlink } from 'node:fs/promises';
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
    '--enable-unattended',
    '--scaffold-root',
    path.join(root, 'scaffolds'),
    '--port',
    String(corePort),
  ],
  {
    windowsHide: true,
    stdio: 'pipe',
    env: { ...process.env, JARVIS_NATIVE_TEST_KEY: 'fixture-not-a-real-api-key' },
  },
);
let app, browser, second, runner, site, siteBrowser;
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
  if (!page)
    throw new Error(
      'Native Jarvis page was not found: ' +
        JSON.stringify(browser.contexts().map((c) => c.pages().map((p) => p.url()))),
    );
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
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page
    .getByLabel('Build goal', { exact: true })
    .fill('Create the selected missing module and satisfy the protected tests');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  await expect(page.locator('.build-job-card')).toContainText('queued');
  const buildJobId = await page.locator('.build-job-card').getAttribute('data-job-id');
  runner = spawn(python, [path.join(repo, 'services/runner/run.pyw'), '--state', root], {
    windowsHide: true,
    stdio: 'pipe',
  });
  await expect(page.locator('.build-job-card')).toContainText('waiting approval', {
    timeout: 30000,
  });
  await page.getByRole('button', { name: /✓Approvals|✓ Approvals/ }).click();
  await page.getByRole('button', { name: /workspace:fixture Review exact action/ }).click();
  await page.getByRole('button', { name: 'Approve exact action' }).click();
  await expect(page.getByRole('status')).toContainText('Decision saved');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await expect(page.locator('.build-job-card')).toContainText('waiting review', { timeout: 30000 });
  await page.getByRole('button', { name: 'Review job proposal' }).click();
  await expect(page.getByRole('region', { name: 'Job proposal review' })).toContainText(
    'feature.py',
  );
  await page.getByRole('button', { name: 'Accept reviewed job repair' }).click();
  await expect(page.getByRole('status')).toContainText('Reviewed repair accepted');
  for (let step = 0; step < 3; step++) {
    await page.getByRole('button', { name: '⚒ Build jobs' }).click();
    await expect(page.getByRole('tab', { name: 'Build jobs', exact: true })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await expect(page.locator('.build-job-card')).toContainText('waiting approval', {
      timeout: 30000,
    });
    await page.getByRole('button', { name: /✓Approvals|✓ Approvals/ }).click();
    await page.getByRole('button', { name: /workspace:fixture Review exact action/ }).click();
    await page.getByRole('button', { name: 'Approve exact action' }).click();
    await expect(page.getByRole('status')).toContainText('Decision saved');
    await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  }
  await expect(page.locator('.build-job-card > strong')).toHaveText('completed · done', {
    timeout: 30000,
  });
  await expect(page.locator('.build-job-card')).toContainText('1/2 model-call slots');
  await page.screenshot({ path: path.join(root, 'native-build-job.png'), fullPage: true });
  await page.getByRole('button', { name: '⌁ Coding runs' }).click();
  await page.getByRole('button', { name: /workspace:fixture Step/ }).click();
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

  await page.getByRole('button', { name: 'Review source delivery', exact: true }).click();
  await expect(page.locator('.delivery-review')).toContainText('feature.py');
  await page.getByRole('button', { name: 'Prepare reviewed delivery' }).click();
  await expect(page.locator('.source-delivery')).toContainText('source:fixture');
  await page.getByRole('button', { name: 'Advance source delivery' }).click();
  await expect(page.getByRole('status')).toContainText('waiting for exact-action approval');
  await page.getByRole('button', { name: /✓Approvals|✓ Approvals/ }).click();
  await page.getByRole('button', { name: /source:fixture Review exact action/ }).click();
  await page.getByRole('button', { name: 'Approve exact action' }).click();
  await expect(page.getByRole('status')).toContainText('Decision saved');
  await page.getByRole('button', { name: '⌁ Coding runs' }).click();
  await page.getByRole('button', { name: /workspace:fixture Step/ }).click();
  await page.getByRole('button', { name: 'Advance source delivery' }).click();
  await expect(page.locator('.source-delivery')).toContainText('succeeded', { timeout: 30000 });
  if (!(await readFile(path.join(root, 'source/feature.py'), 'utf8')).includes('return 42'))
    throw new Error('Reviewed source delivery did not create the tested module');
  await page.getByRole('button', { name: 'Inspect delivery evidence' }).click();
  await expect(page.locator('.delivery-evidence-output')).toContainText('delivered');
  await page.screenshot({ path: path.join(root, 'native-delivery.png'), fullPage: true });

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

  await page.getByText('New project scaffold', { exact: true }).click();
  await page.getByLabel('Scaffold project name', { exact: true }).fill('native-client-service');
  const siteHtml =
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Native client site</title></head><body><main><h1>Native site ready</h1></main></body></html>\n';
  await page
    .getByLabel('Scaffold project template', { exact: true })
    .selectOption('python-web-service-v1');
  await page.getByLabel('Scaffold acceptance examples', { exact: true }).fill(
    JSON.stringify({
      cases: [
        {
          name: 'home',
          input: { method: 'GET', path: '/', body: '' },
          output: { status: 200, content_type: 'text/html; charset=utf-8', body: siteHtml },
        },
        {
          name: 'health',
          input: { method: 'GET', path: '/health', body: '' },
          output: { status: 200, content_type: 'application/json', body: '{"status":"ok"}' },
        },
      ],
    }),
  );
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  const scaffoldReview = page.getByRole('region', { name: 'Scaffold file review' });
  await expect(scaffoldReview).toContainText(path.join(root, 'scaffolds', 'native-client-service'));
  const scaffoldFormGeometry = await page
    .locator('.scaffold-panel fieldset')
    .evaluate((element) => ({
      height: element.clientHeight,
      content: element.scrollHeight,
    }));
  if (scaffoldFormGeometry.content > scaffoldFormGeometry.height + 1)
    throw new Error('Scaffold form has a nested vertical clipping area');
  await expect(
    page.getByRole('button', { name: 'Create reviewed project', exact: true }),
  ).toBeDisabled();
  await scaffoldReview.getByText('app.py', { exact: true }).click();
  await expect(
    scaffoldReview.locator('pre').filter({ hasText: 'NotImplementedError' }),
  ).toBeVisible();
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  await scaffoldReview
    .getByRole('heading', { name: 'Review every planned file', exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-scaffold-review.png'), fullPage: true });
  await page.getByRole('button', { name: 'Create reviewed project', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Project creation receipt', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Check creation receipt', exact: true }).click();
  await expect(page.getByRole('status', { name: 'Scaffold creation receipt' })).not.toContainText(
    'audit event is missing',
  );
  const scaffoldManifest = JSON.parse(
    await readFile(path.join(root, 'scaffolds/native-client-service/scaffold.json'), 'utf8'),
  );
  if (
    scaffoldManifest.registration_draft.execution.owner_enabled !== false ||
    Object.keys(scaffoldManifest.plan.document_provenance).length !== 9 ||
    !(
      await readFile(path.join(root, 'scaffolds/native-client-service/source/app.py'), 'utf8')
    ).includes('NotImplementedError')
  )
    throw new Error('Native scaffold receipt or unimplemented baseline mismatch');
  for (const [name, content] of Object.entries(exportedDocs)) {
    if (
      (await readFile(
        path.join(root, 'scaffolds/native-client-service/source/docs', name),
        'utf8',
      )) !== content
    )
      throw new Error('Scaffold did not preserve approved specification documents');
  }
  await page
    .getByRole('heading', { name: 'Project creation receipt', exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-scaffold-created.png'), fullPage: true });

  const projectFlow = page.getByRole('region', { name: 'Project build workflow' });
  await projectFlow
    .getByRole('button', { name: 'Review workspace registration', exact: true })
    .click();
  await expect(
    projectFlow.getByRole('button', { name: 'Register reviewed workspace', exact: true }),
  ).toBeDisabled();
  await projectFlow
    .getByLabel('I reviewed the workspace, source and fixed native test command.')
    .check();
  await projectFlow
    .getByRole('button', { name: 'Register reviewed workspace', exact: true })
    .click();
  await projectFlow
    .getByLabel('Scaffold execution permission mode', { exact: true })
    .selectOption('full');
  await projectFlow.getByLabel('I reviewed the permission mode and exact resource grants.').check();
  await projectFlow
    .getByRole('button', { name: 'Apply reviewed project permissions', exact: true })
    .click();
  await projectFlow.getByLabel('Allow model calls for this job', { exact: true }).check();
  await projectFlow
    .getByLabel('Automatically accept validated repair proposals', { exact: true })
    .check();
  await projectFlow.getByRole('button', { name: 'Queue model repair job', exact: true }).click();
  await expect(projectFlow.locator('.build-job-card > strong')).toHaveText('completed · done', {
    timeout: 90000,
  });
  await expect(projectFlow.locator('.build-job-card')).toContainText('2/2 model-call slots');
  const newProjectJob = await projectFlow.locator('.build-job-card').getAttribute('data-job-id');
  if (
    !(
      await readFile(path.join(root, 'scaffolds/native-client-service/source/app.py'), 'utf8')
    ).includes('NotImplementedError')
  )
    throw new Error('New project source changed before delivery review');
  await projectFlow.locator('.build-job-card > strong').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-project-built.png'), fullPage: true });
  await expect(page.getByRole('button', { name: 'Edit project permissions' })).toContainText(
    'full',
    { timeout: 30000 },
  );
  await page.getByRole('button', { name: 'Edit project permissions' }).click();
  await page.getByRole('combobox', { name: 'Permission mode', exact: true }).selectOption('ask');
  await page.getByRole('button', { name: 'Save permission policy' }).click();
  await expect(
    page.getByRole('status').filter({ hasText: 'Permission policy updated' }),
  ).toBeVisible();
  await projectFlow
    .getByRole('button', { name: 'Refresh project registration', exact: true })
    .click();
  await projectFlow.getByRole('button', { name: 'Review source delivery', exact: true }).click();
  await projectFlow.getByRole('button', { name: 'Prepare reviewed delivery', exact: true }).click();
  await projectFlow.getByRole('button', { name: 'Advance source delivery', exact: true }).click();
  await expect(projectFlow).toContainText('waiting for exact-action approval');
  await page.getByRole('button', { name: /✓Approvals|✓ Approvals/ }).click();
  await page
    .getByRole('button', { name: /source:native-client-service Review exact action/ })
    .click();
  await page.getByRole('button', { name: 'Approve exact action' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Decision saved' })).toBeVisible();
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  // Panel navigation intentionally discards local selection. Recover the durable
  // specification, receipt, registration, job and prepared delivery without replay.
  await page.locator('.conversations .list-panel .item').first().click();
  await page.getByRole('button', { name: 'Version 2 approved', exact: true }).click();
  await page.getByText('New project scaffold', { exact: true }).click();
  await page.getByLabel('Scaffold project name', { exact: true }).fill('native-client-service');
  await page.getByRole('button', { name: 'Check creation receipt', exact: true }).click();
  await projectFlow.getByRole('button', { name: 'Advance source delivery', exact: true }).click();
  await expect(projectFlow.locator('.source-delivery')).toContainText('succeeded');
  if (
    (await readFile(
      path.join(root, 'scaffolds/native-client-service/source/index.html'),
      'utf8',
    )) !== siteHtml
  )
    throw new Error('Reviewed website delivery did not preserve expected HTML');
  const sourceDirectory = path.join(root, 'scaffolds/native-client-service/source');
  site = spawn(
    python,
    [
      '-I',
      '-B',
      '-c',
      'import sys;sys.path.insert(0,".");from server import serve;s=serve(0);print(s.server_port,flush=True);s.serve_forever()',
    ],
    { cwd: sourceDirectory, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] },
  );
  const sitePort = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Reviewed website did not start')), 10000);
    site.stdout.once('data', (chunk) => {
      clearTimeout(timer);
      resolve(Number(chunk.toString().trim()));
    });
    site.once('error', reject);
  });
  siteBrowser = await chromium.launch({ channel: 'msedge', headless: true });
  const sitePage = await siteBrowser.newPage();
  await sitePage.goto(`http://127.0.0.1:${sitePort}/`);
  await expect(
    sitePage.getByRole('heading', { name: 'Native site ready', exact: true }),
  ).toBeVisible();
  const health = await sitePage.request.get(`http://127.0.0.1:${sitePort}/health`);
  if ((await health.json()).status !== 'ok') throw new Error('Delivered website API failed');
  await sitePage.screenshot({
    path: path.join(root, 'native-delivered-website.png'),
    fullPage: true,
  });
  await expect(sitePage.locator('meta[name="viewport"]')).toHaveAttribute(
    'content',
    /width=device-width/,
  );
  await sitePage.setViewportSize({ width: 375, height: 812 });
  if (!(await sitePage.evaluate(() => document.body.scrollWidth <= window.innerWidth)))
    throw new Error('Delivered website overflows the mobile viewport');
  await sitePage.screenshot({
    path: path.join(root, 'native-delivered-website-mobile.png'),
    fullPage: true,
  });

  await siteBrowser.close();
  siteBrowser = null;
  site.kill();

  await page.getByRole('button', { name: '≋ Activity' }).click();
  await expect(
    page.getByRole('heading', { name: 'Unattended operations', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('region', { name: 'Runner contact' })).toContainText(
    /Worker contact: (recent|in progress)/,
  );
  const outcomeInbox = page.getByRole('region', { name: 'Persistent outcome inbox' });
  const completedWebsite = outcomeInbox
    .locator('article')
    .filter({ hasText: 'native-client-service' })
    .filter({ hasText: 'tested repair ready' })
    .first();
  await expect(completedWebsite).toContainText('2/2 reserved model-call slots');
  const websiteNoticeId = await completedWebsite.getAttribute('data-notice-id');
  await completedWebsite.getByRole('button', { name: 'Acknowledge outcome', exact: true }).click();
  await page.getByRole('button', { name: 'Refresh operations', exact: true }).click();
  await expect(outcomeInbox.locator(`[data-notice-id="${websiteNoticeId}"]`)).toContainText(
    'Acknowledged',
  );
  await page
    .getByRole('region', { name: 'Registered project library' })
    .getByRole('button', { name: 'Open project workflow', exact: true })
    .click();
  const savedWorkflow = page.getByRole('region', { name: 'Saved project workflow' });
  await expect(savedWorkflow.locator('.build-job-card > strong')).toHaveText('completed · done');
  await expect(savedWorkflow.locator('.source-delivery')).toContainText('succeeded');
  await savedWorkflow
    .getByRole('heading', { name: 'native-client-service', exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-operations-library.png'), fullPage: true });
  await page.getByRole('button', { name: 'Close project workflow', exact: true }).click();

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
  await expect(
    page.getByRole('status').filter({ hasText: 'Window arrangement saved' }),
  ).toBeVisible();
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
  // Queue real work while the worker is stopped, then restart it only after
  // the dashboard exits. This proves persisted work, not just a heartbeat.
  await writeFile(path.join(root, 'runner.stop'), 'stop');
  for (let i = 0; i < 80 && runner.exitCode === null; i++) await pause(250);
  if (runner.exitCode !== 0) throw new Error('Isolated runner did not stop cleanly');
  await unlink(path.join(root, 'runner.stop'));
  await page.getByRole('button', { name: 'Edit project permissions' }).click();
  await page.getByRole('combobox', { name: 'Permission mode', exact: true }).selectOption('full');
  await page.getByRole('button', { name: 'Save permission policy' }).click();
  await expect(
    page.getByRole('status').filter({ hasText: 'Permission policy updated' }),
  ).toBeVisible();
  await writeFile(path.join(root, 'snapshot/files/feature.py'), 'def answer():\n    return 41\n');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page.getByText('Configure another repair job', { exact: true }).click();
  await page.getByLabel('Build workspace', { exact: true }).selectOption('workspace:fixture');
  await page.getByLabel('Build test profile', { exact: true }).selectOption('fixture-unit');
  await page
    .getByLabel('Build goal', { exact: true })
    .fill('Overnight fixture repair after dashboard exit');
  const scheduledStart = Math.ceil(Date.now() / 1000) + 30;
  const localStart = new Date(scheduledStart * 1000 - new Date().getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 19)
    .replace(/:00$/, '');
  await page.getByLabel('Schedule build start', { exact: true }).check();
  await page.getByLabel('Scheduled build start time', { exact: true }).fill(localStart);
  await page.getByLabel('Scheduled build start window', { exact: true }).fill('1');
  await page.getByLabel('Review scheduled build conditions', { exact: true }).check();
  await page.getByLabel('Scheduled build start time', { exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-scheduled-review.png'), fullPage: true });
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByLabel('Automatically accept validated repair proposals').check();
  await page.getByRole('button', { name: 'Queue model repair job', exact: true }).click();
  const overnightCard = page
    .locator('.build-job-card')
    .filter({ hasText: 'Overnight fixture repair after dashboard exit' });
  await expect(overnightCard.locator(':scope > strong')).toHaveText('scheduled · baseline');
  const overnightJob = await overnightCard.getAttribute('data-job-id');
  await overnightCard.scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-scheduled-queued.png'), fullPage: true });
  const inspectOvernight = () => {
    const result = spawnSync(
      python,
      [
        '-c',
        'import sqlite3,json,sys;c=sqlite3.connect(sys.argv[1]);c.row_factory=sqlite3.Row;r=dict(c.execute("SELECT state,calls,run,next_due,steps,baseline_task FROM build_jobs WHERE id=?",(sys.argv[2],)).fetchone());r["notices"]=c.execute("SELECT COUNT(*) FROM operation_notices WHERE subject=? AND json_extract(payload,\'$.state\')=\'completed\'",(sys.argv[2],)).fetchone()[0];r["source_tasks"]=c.execute("SELECT COUNT(*) FROM tasks WHERE resource=\'source:fixture\' AND action=\'write\'").fetchone()[0];r["contact_started"]=c.execute("SELECT started FROM runner_contacts WHERE project=(SELECT project FROM build_jobs WHERE id=?)",(sys.argv[2],)).fetchone()[0];print(json.dumps(r));c.close()',
        path.join(root, 'core.sqlite3'),
        overnightJob,
      ],
      { encoding: 'utf8', windowsHide: true, timeout: 10000 },
    );
    if (result.status !== 0) throw new Error('Unable to inspect isolated overnight job');
    return JSON.parse(result.stdout);
  };
  const beforeOvernight = inspectOvernight();
  if (beforeOvernight.state !== 'queued') throw new Error('Work started before dashboard exit');
  if (beforeOvernight.next_due !== scheduledStart)
    throw new Error('Scheduled start was not persisted exactly');
  const heartbeatBeforeExit = JSON.parse(
    await readFile(path.join(root, 'runner-status.json'), 'utf8'),
  );
  await browser.close();
  browser = null;
  app.kill();
  for (let i = 0; i < 30 && app.exitCode === null; i++) await pause(100);
  const restartedAt = Date.now() / 1000;
  runner = spawn(python, [path.join(repo, 'services/runner/run.pyw'), '--state', root], {
    windowsHide: true,
    stdio: 'pipe',
  });
  await expect
    .poll(() => inspectOvernight().contact_started, { timeout: 15000 })
    .toBeGreaterThanOrEqual(restartedAt);
  const beforeScheduledStart = inspectOvernight();
  if (
    Date.now() / 1000 >= scheduledStart ||
    beforeScheduledStart.state !== 'queued' ||
    beforeScheduledStart.calls !== 0 ||
    beforeScheduledStart.steps !== 0 ||
    beforeScheduledStart.baseline_task !== null
  )
    throw new Error('Worker did not preserve the future start without early execution');
  await expect
    .poll(() => inspectOvernight().state, { timeout: 90000, intervals: [1000, 2000] })
    .toBe('completed');
  const afterOvernight = inspectOvernight();
  if (
    afterOvernight.calls !== 1 ||
    afterOvernight.notices !== 1 ||
    afterOvernight.source_tasks !== beforeOvernight.source_tasks
  )
    throw new Error(
      'Overnight repair did not preserve bounded calls, durable outcome and separate delivery',
    );
  const heartbeatAfterExit = JSON.parse(
    await readFile(path.join(root, 'runner-status.json'), 'utf8'),
  );
  if (
    runner.exitCode !== null ||
    core.exitCode !== null ||
    heartbeatAfterExit.at <= heartbeatBeforeExit.at
  )
    throw new Error('Hidden runner did not remain active after desktop exit');
  const reopenedPort = await port();
  app = spawn(executable, [], {
    windowsHide: false,
    stdio: 'pipe',
    env: {
      ...process.env,
      JARVIS_DESKTOP_CONFIG: path.join(root, 'desktop.json'),
      JARVIS_EXPORT_ROOT: path.join(root, 'exports'),
      WEBVIEW2_USER_DATA_FOLDER: path.join(root, 'webview-profile'),
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-address=127.0.0.1 --remote-debugging-port=${reopenedPort}`,
    },
  });
  let reopenedEndpoint;
  for (let i = 0; i < 120; i++) {
    try {
      reopenedEndpoint = await (
        await fetch(`http://127.0.0.1:${reopenedPort}/json/version`)
      ).json();
      if (reopenedEndpoint.webSocketDebuggerUrl) break;
    } catch {}
    await pause(250);
  }
  if (!reopenedEndpoint?.webSocketDebuggerUrl)
    throw new Error('Reopened dashboard was unavailable');
  browser = await chromium.connectOverCDP(reopenedEndpoint.webSocketDebuggerUrl);
  for (let i = 0; i < 60; i++) {
    page = browser
      .contexts()
      .flatMap((c) => c.pages())
      .find((p) => p.url().includes('tauri.localhost'));
    if (page) break;
    await pause(250);
  }
  await expect(page.getByText('Local core connected', { exact: true })).toBeVisible({
    timeout: 30000,
  });
  await page.getByRole('button', { name: '≋ Activity' }).click();
  const overnightNotice = page
    .getByRole('region', { name: 'Persistent outcome inbox' })
    .locator('article')
    .filter({ hasText: 'Overnight fixture repair after dashboard exit' });
  await expect(overnightNotice).toContainText('completed');
  await expect(overnightNotice).toContainText('1/2 reserved model-call slots');
  await overnightNotice.getByRole('button', { name: 'Acknowledge outcome', exact: true }).click();
  await expect(overnightNotice).toContainText('Acknowledged');
  await overnightNotice.getByRole('heading').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(root, 'native-overnight-outcome.png'), fullPage: true });
  const summary = {
    fixture: true,
    isolated_webview_profile: true,
    live_model_calls: 0,
    project: fixture.project,
    seed_proposal: fixture.proposal,
    build_job: buildJobId,
    native_core_connected: true,
    dpapi_credentials: true,
    permission_policy_saved: true,
    frontend_asset: expectedAsset,
    approval_gates: 4,
    source_delivery_approval_gates: 1,
    run_state: 'ready_for_review',
    evidence_reports: 4,
    source_preserved: sourcePreserved,
    reviewed_new_file_created_and_tested: true,
    reviewed_source_delivery_verified: true,
    model_build_job_completed_by_hidden_runner: true,
    exact_model_proposal_reviewed: true,
    model_call_slots_reserved: 1,
    hidden_runner_survives_desktop_exit: true,
    conversation_saved: true,
    model_chat_completed: true,
    structured_plan_completed: true,
    versioned_specification_approved: true,
    specification_revision_and_export_verified: true,
    reviewed_native_scaffold_creation_verified: true,
    scaffold_execution_not_enabled_at_creation: true,
    reviewed_workspace_registered_in_database: true,
    operations_inbox_acknowledgement_persisted: true,
    saved_project_reopened_from_library: true,
    queued_job_completed_after_dashboard_exit_and_worker_restart: true,
    overnight_job: overnightJob,
    overnight_model_calls_reserved: afterOvernight.calls,
    scheduled_start_utc: scheduledStart,
    scheduled_worker_contact_before_due_verified: true,
    scheduled_not_before_enforced: true,
    runner_contact_reported_in_native_ui: true,
    overnight_outcome_visible_after_dashboard_restart: true,
    overnight_source_delivery_not_dispatched: true,
    new_project_build_job: newProjectJob,
    new_project_failed_repair_then_successful_cycle: true,
    new_project_model_call_slots: 2,
    reviewed_website_delivery_and_browser_verified: true,
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
  if (siteBrowser) await siteBrowser.close().catch(() => {});
  if (site && site.exitCode === null) site.kill();
  if (browser) await browser.close().catch(() => {});
  if (app && app.exitCode === null) app.kill();
  if (second && second.exitCode === null) second.kill();
  if (core.exitCode === null) core.kill();
  if (runner && runner.exitCode === null) runner.kill();
}
