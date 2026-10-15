import { test, expect } from '@playwright/test';

test('browser without preview never connects or shows sample project state', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', (req) => {
    if (req.url().includes('/v1/')) requests.push(req.url());
  });
  await page.goto('/');
  await expect(
    page.getByText('Set up the private Windows connection', { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: '＋ New project', exact: true })).toBeDisabled();
  await expect(page.getByText('VISUAL PREVIEW', { exact: false })).toHaveCount(0);
  expect(requests).toEqual([]);
});

test('canvas shows connected, configured and planned systems truthfully', async ({ page }) => {
  await page.goto('/?preview=1');
  await expect(page.getByText('VISUAL PREVIEW', { exact: false })).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'One workspace. Every capability.' }),
  ).toBeVisible();
  await expect(page.getByText('Local core connected')).toBeVisible();
  await page.getByRole('button', { name: 'G Google Workspace Planned' }).click();
  await expect(
    page.getByText('Reusable Google service integration is not connected to this core.'),
  ).toBeVisible();
  await expect(page.locator('.react-flow__minimap-node')).toHaveCount(9);
  const mapSizes = await page
    .locator('.react-flow__minimap-node')
    .evaluateAll((nodes) =>
      nodes.map((node) => [
        Number(node.getAttribute('width')),
        Number(node.getAttribute('height')),
      ]),
    );
  expect(mapSizes.every(([width, height]) => width > 0 && height > 0)).toBe(true);
  await page.screenshot({ path: 'test-results/subsystem-canvas.png', fullPage: true });
});

test('proposal review exposes selected context and exact patch before acceptance', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◇ Repair proposals' }).click();
  await page.getByRole('button', { name: 'workspace:demo gemini-3.5-flash-lite ready' }).click();
  await expect(
    page.getByText('Remove the extra subtraction from the total calculation.'),
  ).toBeVisible();
  await expect(page.getByText('Protected test', { exact: true })).toBeVisible();
  await expect(page.locator('.removed')).toHaveText('− sum(items) - 1');
  await page.getByRole('button', { name: 'Accept into coding run' }).click();
  await expect(page.getByRole('status')).toContainText('Proposal accepted');
  await expect(page.getByRole('button', { name: 'Accept into coding run' })).toHaveCount(0);
});

test('exact-action approval can be rejected without widening permissions', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: /✓Approvals|✓ Approvals/ }).click();
  await page.getByRole('button', { name: /execute · workspace:demo/ }).click();
  await expect(page.getByText('Policy version', { exact: true })).toBeVisible();
  await expect(page.locator('pre')).toContainText('"profile": "unit"');
  await page.getByRole('button', { name: 'Reject', exact: true }).click();
  await expect(page.getByText('No pending approval requests.')).toBeVisible();
});

test('conversation treats markup as text and stores a user message', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  const text = '<img src=x onerror=alert(1)> Remember this project requirement.';
  await page.getByLabel('Message', { exact: true }).fill(text);
  await page.getByRole('button', { name: 'Save message', exact: true }).click();
  await expect(page.getByText(text, { exact: true })).toBeVisible();
  await expect(page.locator('.messages img')).toHaveCount(0);
});

test('run inspection shows checkpoints and explicit cancellation state', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⌁ Coding runs' }).click();
  await page.getByRole('button', { name: /workspace:demo Step 0/ }).click();
  await expect(page.locator('.steps li')).toHaveCount(4);
  await page.getByRole('button', { name: 'Cancel run', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Advance one step' })).toBeDisabled();
  await expect(page.locator('.detail .panel-heading')).toContainText('cancelled');
});

test('new proposal requires explicit files and keyboard dialog can close', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◇ Repair proposals' }).click();
  await page.getByRole('button', { name: '＋ New proposal' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Goal', { exact: true }).fill('Correct the calculation');
  await expect(page.getByRole('button', { name: 'Prepare proposal', exact: true })).toBeDisabled();
  await page.getByLabel('src/totals.py', { exact: true }).check();
  await expect(page.getByRole('button', { name: 'Prepare proposal', exact: true })).toBeEnabled();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: '＋ New proposal' })).toBeFocused();
});

test('new project remains a project dialog while viewing repairs', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◇ Repair proposals' }).click();
  await page.getByRole('button', { name: '＋ New project', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Create project', exact: true })).toBeVisible();
  await expect(page.getByLabel('Project name', { exact: true })).toBeFocused();
});

test('narrow Windows layout keeps subsystem details accessible', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 800 });
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: 'G Google Workspace Planned' }).click();
  await expect(
    page.getByText('Reusable Google service integration is not connected to this core.'),
  ).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('owner can review exact grants and change project permission mode', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: 'Edit project permissions' }).click();
  await page
    .getByRole('combobox', { name: 'Permission mode', exact: true })
    .selectOption('read_only');
  await expect(page.getByRole('group', { name: 'Exact resource grants' })).toContainText(
    'workspace:demo',
  );
  await page.getByRole('button', { name: 'Save permission policy' }).click();
  await expect(page.getByRole('status')).toContainText('Permission policy updated');
  await expect(page.getByRole('button', { name: 'Edit project permissions' })).toContainText(
    'read only',
  );
});

test('cancellation remains available while a run request is in flight', async ({ page }) => {
  await page.goto('/?preview=1&slow=1');
  await page.getByRole('button', { name: '⌁ Coding runs' }).click();
  await page.getByRole('button', { name: /workspace:demo Step 0/ }).click();
  await page.getByRole('button', { name: 'Advance one step' }).click();
  await expect(page.getByRole('button', { name: 'Cancel run', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Cancel run', exact: true }).click();
  await expect(page.getByRole('button', { name: '↻ Reconnect', exact: true })).toBeEnabled();
  await expect(page.locator('.detail .panel-heading')).toContainText('cancelled');
});

test('connected core with no projects prompts creation without claiming disconnection', async ({
  page,
}) => {
  await page.goto('/?preview=1&empty=1');
  await expect(page.getByText('Local core connected')).toBeVisible();
  await expect(page.getByRole('status')).toContainText('Create a project to begin');
  await expect(page.getByRole('button', { name: '＋ New project', exact: true })).toBeEnabled();
});

test('permission review stays bound to its opening version after a background refresh', async ({
  page,
}) => {
  await page.goto('/?preview=1&stale=1');
  await page.getByRole('button', { name: 'Edit project permissions' }).click();
  await expect(page.getByText('Reviewed policy v3.', { exact: false })).toBeVisible();
  await page
    .getByRole('combobox', { name: 'Permission mode', exact: true })
    .selectOption('read_only');
  await expect(page.locator('.page-footer')).toContainText('Policy v4', { timeout: 15000 });
  await page.getByRole('button', { name: 'Save permission policy' }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('state changed');
  await expect(page.getByRole('button', { name: 'Edit project permissions' })).toContainText('ask');
});

test('chat explicitly selects an online model and persists the reply with usage', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('chat');
  await page.getByLabel('Message', { exact: true }).fill('What should we build first?');
  await expect(page.getByRole('button', { name: 'Send to model', exact: true })).toBeDisabled();
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByRole('button', { name: 'Send to model', exact: true }).click();
  await expect(page.locator('.model-reply')).toHaveText('Fixture response for human review.');
  await expect(page.locator('.usage')).toContainText('total tokens: 42');
  await page.getByText('Context sent to the model', { exact: true }).click();
  await expect(page.locator('.model-result pre')).toContainText('What should we build first?');
  await expect(page.locator('.model-result')).toContainText(
    '2 history messages included; 0 omitted.',
  );
});

test('project plan has requirements, phases and acceptance without starting a run', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('plan');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByLabel('Message', { exact: true }).fill('Plan a responsive client website.');
  await page.getByRole('button', { name: 'Generate draft plan', exact: true }).click();
  await expect(page.locator('.project-plan')).toContainText('Draft · review required');
  await expect(page.getByRole('heading', { name: 'Client website delivery' })).toBeVisible();
  await expect(page.locator('.project-plan')).toContainText('Acceptance criteria');
  await expect(page.locator('.project-plan')).toContainText('Who supplies final content?');
  await expect(page.getByRole('button', { name: /Execute plan|Start build/ })).toHaveCount(0);
  await expect(page.locator('.conversations')).toHaveCSS('display', 'grid');
  await page.screenshot({ path: 'test-results/project-plan.png', fullPage: true });
  await page.setViewportSize({ width: 900, height: 850 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('interrupt model request stays terminal when its late response arrives', async ({ page }) => {
  await page.goto('/?preview=1&slowchat=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('chat');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByLabel('Message', { exact: true }).fill('Slow response fixture');
  await page.getByRole('button', { name: 'Send to model', exact: true }).click();
  await page.getByRole('button', { name: 'Interrupt model request', exact: true }).click();
  await expect(page.locator('.model-result .pill')).toHaveText('interrupted');
  await expect(page.getByLabel('Response mode')).toBeEnabled();
  await expect(page.locator('.model-result .pill')).toHaveText('interrupted');
  await expect(page.locator('.model-reply')).toHaveCount(0);
  await expect(page.locator('.messages .assistant')).toHaveCount(1);
});

test('failed model request shows a safe error and offers no replay button', async ({ page }) => {
  await page.goto('/?preview=1&failchat=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('chat');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByLabel('Message', { exact: true }).fill('Failed response fixture');
  await page.getByRole('button', { name: 'Send to model', exact: true }).click();
  await expect(page.locator('.model-result')).toContainText('provider_http_429');
  await expect(page.locator('.model-result')).toContainText('this request will not be replayed');
  await expect(page.getByRole('button', { name: 'Send prepared request once' })).toHaveCount(0);
});

test('setup reads readiness and missing models block chat without blocking notes', async ({
  page,
}) => {
  await page.goto('/?preview=1&nomodel=1');
  await page.getByRole('button', { name: '⚙ Setup' }).click();
  await expect(page.getByRole('heading', { name: 'Set up your workspace' })).toBeVisible();
  await expect(page.getByText('No online models are registered.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('chat');
  await page.getByLabel('Message', { exact: true }).fill('No configured model');
  await expect(page.getByRole('button', { name: 'Send to model', exact: true })).toBeDisabled();
  await page.getByLabel('Response mode').selectOption('note');
  await expect(page.getByRole('button', { name: 'Save message', exact: true })).toBeEnabled();
});
