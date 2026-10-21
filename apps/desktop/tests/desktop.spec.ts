import { test, expect } from '@playwright/test';

test('build guidance pins revisions and renews consent after host changes', async ({ page }) => {
  await page.goto('/?preview=1&skilldrift=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('Use reviewed guidance');
  const skill = page.getByLabel('Use skill minimal-repair', { exact: true });
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await skill.check();
  await expect(
    page.getByLabel('Allow model calls for this job', { exact: true }),
  ).not.toBeChecked();
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.evaluate(() => sessionStorage.setItem('fixture.skill-revision', 'updated'));
  await page.getByRole('button', { name: '↻ Reconnect', exact: true }).click();
  await expect(
    page.getByText(
      'Selected guidance changed. Review and select the current revision before continuing.',
    ),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Queue model repair job' })).toBeDisabled();
  await expect(
    page.getByLabel('Allow model calls for this job', { exact: true }),
  ).not.toBeChecked();
  await skill.uncheck();
  await skill.check();
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  await expect(page.locator('.job-guidance')).toContainText('minimal-repair · 222222222222');
});

test('coding guidance selection stays bounded to five explicit skills', async ({ page }) => {
  await page.goto('/?preview=1&manyskills=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  for (let index = 1; index <= 5; index++)
    await page.getByLabel(`Use skill skill-${index}`, { exact: true }).check();
  await expect(page.getByLabel('Use skill skill-6', { exact: true })).toBeDisabled();
  await page.getByLabel('Use skill skill-1', { exact: true }).uncheck();
  await expect(page.getByLabel('Use skill skill-6', { exact: true })).toBeEnabled();
});

test('proposal preparation shares the explicit trusted guidance selector', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◇ Repair proposals', exact: true }).click();
  await page.getByRole('button', { name: '＋ New proposal', exact: true }).click();
  await expect(
    page.getByRole('group', { name: 'Trusted coding guidance · optional' }),
  ).toBeVisible();
  await page.getByLabel('Use skill minimal-repair', { exact: true }).check();
  await expect(page.getByLabel('Use skill minimal-repair', { exact: true })).toBeChecked();
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
});

test('failed generation recovery requires fresh explicit consent and keeps the call budget', async ({
  page,
}) => {
  await page.goto('/?preview=1&failedgeneration=invalid_model_response');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('Recover a known invalid response');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  const recovery = page.getByRole('region', { name: 'Failed generation recovery' });
  await recovery.getByRole('button', { name: 'Review failed generation' }).click();
  await expect(recovery).toContainText('invalid_json');
  const retry = recovery.getByRole('button', { name: 'Queue reviewed generation retry' });
  await expect(retry).toBeDisabled();
  await recovery.getByLabel('Allow one new model generation').check();
  await recovery.getByRole('button', { name: 'Review failed generation' }).click();
  await expect(retry).toBeDisabled();
  await recovery.getByLabel('Allow one new model generation').check();
  await retry.click();
  await expect(recovery).toHaveCount(0);
  await expect(page.locator('.build-job-card')).toContainText('1/2 model-call slots · Cycle 2/2');
});

test('uncertain generation failures do not offer a retry', async ({ page }) => {
  await page.goto('/?preview=1&failedgeneration=generation_failed');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('Inspect uncertain transport failure');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  await expect(page.locator('.build-job-card')).toContainText('failed');
  await expect(page.getByRole('button', { name: 'Review failed generation' })).toHaveCount(0);
});

test('repair jobs require explicit model consent and an exact proposal review', async ({
  page,
}) => {
  await page.goto('/?preview=1&buildreview=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page
    .getByLabel('Build goal', { exact: true })
    .fill('Repair the selected total calculation');
  await expect(page.getByRole('button', { name: 'Queue model repair job' })).toBeDisabled();
  await expect(page.getByLabel('Automatically accept validated repair proposals')).toBeDisabled();
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  await expect(page.locator('.build-job-card')).toContainText('waiting review');
  await page.getByRole('button', { name: 'Review job proposal' }).click();
  await expect(page.getByRole('region', { name: 'Job proposal review' })).toContainText(
    'src/totals.py',
  );
  await page.getByRole('button', { name: 'Accept reviewed job repair' }).click();
  await expect(page.locator('.build-job-card')).toContainText('queued · execute');
  await page.getByRole('button', { name: 'Pause repair job' }).click();
  await expect(page.locator('.build-job-card')).toContainText('paused');
  await page.getByRole('button', { name: 'Cancel repair job' }).click();
  await expect(page.locator('.build-job-card')).toContainText('cancelled');
});

test('long-running jobs show observed supervision and retain cancellation', async ({ page }) => {
  await page.goto('/?preview=1&runningbuild=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('Run the reviewed long build');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  const status = page.getByRole('region', { name: 'Dispatch supervision' });
  await expect(status).toContainText('Dispatch lease active');
  await expect(status).toContainText('610 seconds elapsed at last refresh');
  await expect(status).toContainText('not proof of successful completion');
  await page.getByRole('button', { name: 'Cancel repair job' }).click();
  await expect(status).toHaveCount(0);
  await expect(page.locator('.build-job-card')).toContainText('cancelled');
});

test('host-disabled repair jobs cannot reserve model calls', async ({ page }) => {
  await page.goto('/?preview=1&runnerdisabled=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await expect(page.getByRole('button', { name: 'Queue model repair job' })).toBeDisabled();
});

test('repair configuration fits narrow windows with compact context checkboxes', async ({
  page,
}) => {
  await page.setViewportSize({ width: 720, height: 900 });
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  const dimensions = await page
    .locator('.build-jobs-panel fieldset')
    .evaluateAll((elements) =>
      elements.map((element) => ({ width: element.clientWidth, scroll: element.scrollWidth })),
    );
  expect(dimensions.length).toBeGreaterThan(0);
  expect(dimensions.every((element) => element.scroll <= element.width + 1)).toBe(true);
  const checkboxes = await page
    .locator('.build-jobs-panel input[type=checkbox]')
    .evaluateAll((nodes) => nodes.map((node) => node.getBoundingClientRect().width));
  expect(checkboxes.every((width) => width > 0 && width <= 24)).toBe(true);
  await page.screenshot({ path: 'test-results/build-job-configuration.png', fullPage: true });
});

test('owner queues, pauses, resumes and cancels a bounded assignment', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◷ Assignments' }).click();
  await page.getByLabel('Assignment goal', { exact: true }).fill('Complete the reviewed fixture');
  await page.getByRole('button', { name: 'Queue unattended assignment' }).click();
  await expect(page.locator('.assignment-card')).toContainText('queued');
  await page.getByRole('button', { name: 'Pause assignment', exact: true }).click();
  await expect(page.locator('.assignment-card')).toContainText('paused');
  await page.getByRole('button', { name: 'Resume assignment', exact: true }).click();
  await expect(page.locator('.assignment-card')).toContainText('queued');
  await page.getByRole('button', { name: 'Cancel assignment', exact: true }).click();
  await expect(page.locator('.assignment-card')).toContainText('cancelled');
  await expect(page.getByRole('button', { name: 'Resume assignment', exact: true })).toBeDisabled();
});

test('host-disabled unattended execution cannot queue assignments', async ({ page }) => {
  await page.goto('/?preview=1&runnerdisabled=1');
  await page.getByRole('button', { name: '◷ Assignments' }).click();
  await expect(page.getByText('Disabled in host configuration', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Queue unattended assignment' })).toBeDisabled();
});

test('source delivery requires a registered target and an explicit reviewed manifest', async ({
  page,
}) => {
  await page.goto('/?preview=1&delivery=1');
  await page.getByRole('button', { name: '⌁ Coding runs' }).click();
  await page.getByRole('button', { name: /workspace:demo Step/ }).click();
  await page.getByRole('button', { name: 'Advance one step' }).click();
  await expect(page.getByRole('button', { name: 'Prepare reviewed delivery' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Review source delivery', exact: true }).click();
  await expect(page.locator('.delivery-review')).toContainText('src/totals.py');
  await expect(page.locator('.delivery-review')).toContainText('a'.repeat(64));
  await page.getByRole('button', { name: 'Prepare reviewed delivery' }).click();
  await expect(page.locator('.source-delivery')).toContainText('source:demo · queued');
  await page.getByRole('button', { name: 'Advance source delivery' }).click();
  await expect(page.locator('.source-delivery')).toContainText('source:demo · succeeded');
  await expect(page.getByRole('button', { name: 'Advance source delivery' })).toBeDisabled();
  const continuation = page.getByRole('region', { name: 'Continue delivered project' });
  await continuation.getByLabel('Next generation name').fill('demo-next');
  await continuation.getByRole('button', { name: 'Review next snapshot' }).click();
  await expect(continuation.locator('.continuation-review')).toContainText('workspace:demo-next');
  await expect(
    continuation.getByRole('button', { name: 'Register reviewed generation' }),
  ).toBeDisabled();
  await continuation
    .getByLabel('Allow this reviewed generation to use the existing native test profile')
    .check();
  await continuation.getByLabel('Next generation name').fill('demo-third');
  await expect(continuation.locator('.continuation-review')).toHaveCount(0);
  await continuation.getByRole('button', { name: 'Review next snapshot' }).click();
  await expect(
    continuation.getByRole('button', { name: 'Register reviewed generation' }),
  ).toBeDisabled();
  await continuation
    .getByLabel('Allow this reviewed generation to use the existing native test profile')
    .check();
  await continuation.getByRole('button', { name: 'Register reviewed generation' }).click();
  await expect(continuation.getByRole('status')).toContainText(
    'Generation registered: workspace:demo-third',
  );
  await continuation.getByRole('button', { name: 'Check generation status' }).click();
  await expect(continuation.getByRole('status')).toContainText(
    'Grant its workspace and source resources',
  );
});

test('an unregistered source cannot be selected from a completed coding run', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⌁ Coding runs' }).click();
  await page.getByRole('button', { name: /workspace:demo Step/ }).click();
  await page.getByRole('button', { name: 'Advance one step' }).click();
  await expect(
    page.getByText('No source target is registered and granted for this workspace.'),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Review source delivery', exact: true }),
  ).toHaveCount(0);
});

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
  await page.getByRole('button', { name: 'Refresh approvals', exact: true }).click();
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

test('coding jobs link to conversation history without adding messages or retaining stale consent', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  const goal = '<img src=x onerror=alert(1)> Build a reusable task tracker';
  await page.getByLabel('Build goal', { exact: true }).fill(goal);
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByLabel('Coding history conversation').selectOption('demo-conversation');
  await expect(page.getByRole('button', { name: 'Queue model repair job' })).toBeDisabled();
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  const history = page.getByRole('region', { name: 'Linked coding history' });
  await history.getByRole('button', { name: 'Load coding history' }).click();
  await expect(history).toContainText(goal);
  await expect(history.locator('img')).toHaveCount(0);
  await expect(page.locator('.messages .message')).toHaveCount(2);
  await history.getByRole('button', { name: 'Refresh coding history' }).click();
  await expect(history.locator('details')).toHaveCount(1);
});

test('coding context is explicit per request and inspectable in the saved turn', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('chat');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  const consent = page.getByRole('checkbox', { name: /Include this conversation/ });
  await expect(consent).not.toBeChecked();
  await consent.check();
  await page.getByLabel('Response mode').selectOption('plan');
  await expect(consent).not.toBeChecked();
  await page.getByLabel('Response mode').selectOption('chat');
  await consent.check();
  await page.getByLabel('Message', { exact: true }).fill('Summarize recorded coding work.');
  await page.getByRole('button', { name: 'Send to model', exact: true }).click();
  await expect(consent).not.toBeChecked();
  await page.getByText('Context sent to the model', { exact: true }).click();
  await expect(page.locator('.model-result')).toContainText(
    'Explicit coding history snapshot: 0 recorded jobs',
  );
  await expect(page.locator('.model-result')).toContainText(
    'Historical status only; no execution permission',
  );
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

test('3D core is keyboard rotatable with optional reduced-motion-safe orbit', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/?preview=1');
  const core = page.getByRole('slider', { name: 'Rotate Jarvis core' });
  await expect(core).toHaveAttribute('aria-valuenow', '24');
  await core.focus();
  await page.keyboard.press('ArrowRight');
  await expect(core).toHaveAttribute('aria-valuenow', '32');
  await page.getByRole('button', { name: 'Pause orbit', exact: true }).click();
  await page.getByRole('button', { name: 'Animate orbit', exact: true }).click();
  await expect(page.locator('.orb-body')).toHaveCSS('animation-name', 'none');
  await page.screenshot({ path: 'test-results/jarvis-3d-workspace.png', fullPage: true });
});

test('orb activity distinguishes observed work and recorded model requests', async ({ page }) => {
  for (const [state, label] of [
    ['testing', 'Running protected tests'],
    ['coding', 'Applying reviewed changes'],
    ['planning', 'Project plan response pending'],
    ['thinking', 'Conversation response pending'],
    ['inspecting', 'Inspecting approved files'],
    ['stopping', 'Stopping current execution'],
    ['queued', 'Work queued'],
    ['paused', 'Work paused'],
    ['blocked', 'Work needs attention'],
  ]) {
    await page.goto(`/?preview=1&coreactivity=${state}`);
    const core = page.getByRole('region', { name: 'Jarvis 3D operating core' });
    await expect(core).toHaveAttribute('data-activity', state);
    await expect(core.getByText(label, { exact: true })).toBeVisible();
    await expect(core.getByText(/Voice not connected/)).toBeVisible();
  }
});

test('orb prioritizes review while disclosing concurrent testing and blocked work', async ({
  page,
}) => {
  await page.goto('/?preview=1&coreactivity=mixed');
  const core = page.getByRole('region', { name: 'Jarvis 3D operating core' });
  await expect(core).toHaveAttribute('data-activity', 'review');
  await expect(core.getByText('Your review is needed', { exact: true })).toBeVisible();
  await expect(
    core.getByText(/1 review · 1 test execution · 1 item needing attention/),
  ).toBeVisible();
});

test('orb does not invent activity for missing or foreign snapshots and disconnected Core', async ({
  page,
}) => {
  for (const state of ['unknown', 'foreign']) {
    await page.goto(`/?preview=1&coreactivity=${state}`);
    const core = page.getByRole('region', { name: 'Jarvis 3D operating core' });
    await expect(core).toHaveAttribute('data-activity', 'unknown');
    await expect(
      core.getByText('Project activity is unavailable from this connection.'),
    ).toBeVisible();
  }
  await page.goto('/');
  await expect(page.getByRole('region', { name: 'Jarvis 3D operating core' })).toHaveAttribute(
    'data-activity',
    'offline',
  );
});

test('orb responds to document visibility events and keeps reduced motion usable', async ({
  page,
}) => {
  await page.goto('/?preview=1&coreactivity=planning');
  const core = page.getByRole('region', { name: 'Jarvis 3D operating core' });
  await page.bringToFront();
  await expect(core).toHaveAttribute('data-animate', 'true');
  await page.evaluate(() => {
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(core).toHaveAttribute('data-animate', 'false');
  await page.evaluate(() => {
    delete (document as unknown as Record<string, unknown>).hidden;
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(core).toHaveAttribute('data-animate', 'true');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(core.locator('.orb-gloss')).toHaveCSS('animation-name', 'none');
  await expect(core.locator('.orb-body')).toHaveCSS('animation-name', 'none');
  await page.setViewportSize({ width: 780, height: 900 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/jarvis-activity-gloss.png', fullPage: true });
});

test('workspace tabs preserve drafts, minimize, reorder and restore after reload', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page
    .getByLabel('Message', { exact: true })
    .fill('Keep this local draft while switching tabs');
  await page.getByLabel('New workspace tab', { exact: true }).click();
  await page.getByLabel('New tab content', { exact: true }).selectOption('Activity');
  await page.getByRole('button', { name: 'Open tab', exact: true }).click();
  await expect(page.getByRole('tab')).toHaveCount(2);
  await page.getByRole('tab', { name: 'Conversations', exact: true }).click();
  await expect(page.getByLabel('Message', { exact: true })).toHaveValue(
    'Keep this local draft while switching tabs',
  );
  await page.getByLabel('Workspace arrangement', { exact: true }).click();
  await page.getByRole('button', { name: 'Minimize tab', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Conversations', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Restore Conversations', exact: true }).click();
  await expect(page.getByLabel('Message', { exact: true })).toHaveValue(
    'Keep this local draft while switching tabs',
  );
  await page.getByRole('tab', { name: 'Activity', exact: true }).click();
  await page.getByLabel('Workspace arrangement', { exact: true }).click();
  await page.getByRole('button', { name: 'Move tab left', exact: true }).click();
  await expect(page.getByRole('tab').first()).toHaveText('Activity');
  await page.reload();
  await expect(page.getByRole('tab').first()).toHaveText('Activity');
  await expect(page.getByRole('tab', { name: 'Activity', exact: true })).toHaveAttribute(
    'aria-selected',
    'true',
  );
});

test('tab keyboard controls and close keep at least one usable panel', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.keyboard.press('Control+t');
  await expect(page.getByRole('tab')).toHaveCount(2);
  await page.getByRole('tab').last().focus();
  await page.keyboard.press('ArrowLeft');
  await expect(page.getByRole('tab').first()).toBeFocused();
  await page.keyboard.press('Control+w');
  await expect(page.getByRole('tab')).toHaveCount(1);
  await page.keyboard.press('Control+w');
  await expect(page.getByRole('tab')).toHaveCount(1);
  await expect(
    page.getByRole('heading', { name: 'One workspace. Every capability.' }),
  ).toBeVisible();
});

test('workspace rejects corrupt saved preferences and keeps native popouts explicit', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.evaluate(() =>
    localStorage.setItem(
      'jarvis.workspace.v1.main',
      '{"version":1,"tabs":[{"view":"https://example.com"}]}',
    ),
  );
  await page.reload();
  await expect(page.getByRole('tab', { name: 'Overview', exact: true })).toBeVisible();
  await page.getByRole('button', { name: '↗ Conversation window', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Open the Jarvis Windows application');
});

test('workspace fits a small native-sized window without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 680, height: 560 });
  await page.goto('/?preview=1');
  await expect(page.getByRole('slider', { name: 'Rotate Jarvis core' })).toBeVisible();
  const sizes = await page
    .locator('.workspace-pane:not([hidden])')
    .evaluate((node) => ({ width: node.clientWidth, scroll: node.scrollWidth }));
  expect(sizes.scroll).toBeLessThanOrEqual(sizes.width);
});

test('core and system map can be focused separately and dashboard cards expose popouts', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await expect(
    page.getByRole('button', { name: 'Open approvals card in new window', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Open system map in new window', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: '◉ Jarvis core', exact: true }).click();
  await expect(page.getByRole('slider', { name: 'Rotate Jarvis core' })).toBeVisible();
  await expect(page.locator('.canvas')).toHaveCount(0);
  await page.getByRole('button', { name: 'Toggle focus layout', exact: true }).click();
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Toggle focus layout', exact: true }).click();
  await page.getByRole('button', { name: '⌁ System map', exact: true }).click();
  await expect(page.locator('.canvas')).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Rotate Jarvis core' })).toHaveCount(0);
});

test('completed plan becomes a versioned reviewed specification and optional repair context', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('plan');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByLabel('Message', { exact: true }).fill('Plan a client website.');
  await page.getByRole('button', { name: 'Generate draft plan', exact: true }).click();
  await page.getByRole('button', { name: 'Save specification version', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Specification version 1 - draft', exact: true }),
  ).toBeVisible();
  await page.getByText('01_PRODUCT_REQUIREMENTS.md', { exact: true }).click();
  await expect(page.locator('pre').filter({ hasText: 'Responsive client website.' })).toBeVisible();
  await page.getByRole('button', { name: 'Approve reviewed specification', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Specification version 1 - approved', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Approve reviewed specification', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Edit as new revision', exact: true }).click();
  const revision = page.getByRole('dialog');
  await expect(
    revision.getByRole('button', { name: 'Save revised draft', exact: true }),
  ).toBeDisabled();
  await revision
    .getByLabel('Document content', { exact: true })
    .fill('# Updated requirements\nOwner reviewed revision.');
  await revision
    .getByLabel('Additional specification document', { exact: true })
    .selectOption('02_SYSTEM_ARCHITECTURE.md');
  await revision.getByRole('button', { name: 'Add document', exact: true }).click();
  await expect(
    revision.getByRole('button', { name: 'Save revised draft', exact: true }),
  ).toBeDisabled();
  await revision
    .getByLabel('Document content', { exact: true })
    .fill('# Architecture\nApproved stack.');
  await revision.getByRole('button', { name: 'Save revised draft', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Specification version 2 - draft', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Export approved documents', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Approve reviewed specification', exact: true }).click();
  await page.getByRole('button', { name: 'Export approved documents', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Preview only - no files written');
  await page.getByRole('button', { name: '◇ Repair proposals' }).click();
  await page.getByRole('button', { name: /New proposal/ }).click();
  await page.getByLabel('Approved specification', { exact: true }).selectOption('spec-1');
  await expect(page.getByLabel('Approved specification', { exact: true })).toHaveValue('spec-1');
});

test('a conflicting revision retains owner edits and can be cancelled with focus restored', async ({
  page,
}) => {
  await page.goto('/?preview=1&stalespec=1');
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('plan');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByLabel('Message', { exact: true }).fill('Plan fixture.');
  await page.getByRole('button', { name: 'Generate draft plan', exact: true }).click();
  await page.getByRole('button', { name: 'Save specification version', exact: true }).click();
  await page.getByRole('button', { name: 'Edit as new revision', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog
    .getByLabel('Document content', { exact: true })
    .fill('Preserve this owner revision after conflict.');
  await dialog.getByRole('button', { name: 'Save revised draft', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('The state changed');
  await expect(dialog.getByLabel('Document content', { exact: true })).toHaveValue(
    'Preserve this owner revision after conflict.',
  );
  await dialog.getByRole('button', { name: 'Cancel revision', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Edit as new revision', exact: true }),
  ).toBeFocused();
});

test('new-file proposals disclose absence and entire content before acceptance', async ({
  page,
}) => {
  await page.goto('/?preview=1&newfile=1');
  await page.getByRole('button', { name: '◇ Repair proposals' }).click();
  await page.getByRole('button', { name: /workspace:demo gemini/ }).click();
  await expect(page.getByText('New file target', { exact: true })).toBeVisible();
  await expect(page.getByText('New file (must not exist)', { exact: true })).toBeVisible();
  await expect(page.locator('.patch .added')).toContainText('def answer():');
  await expect(
    page.getByRole('button', { name: 'Accept into coding run', exact: true }),
  ).toBeEnabled();
});

async function approvedScaffold(page: import('@playwright/test').Page, query = '') {
  await page.goto('/?preview=1' + query);
  await page.getByRole('button', { name: '◌ Conversations' }).click();
  await page.getByRole('button', { name: /Conversation demo-con/ }).click();
  await page.getByLabel('Response mode').selectOption('plan');
  await page.getByLabel('Online model').selectOption('gemini-repair');
  await page.getByLabel('Message', { exact: true }).fill('Plan a reviewed JSON function.');
  await page.getByRole('button', { name: 'Generate draft plan', exact: true }).click();
  await page.getByRole('button', { name: 'Save specification version', exact: true }).click();
  await page.getByRole('button', { name: 'Approve reviewed specification', exact: true }).click();
  await page.getByText('New project scaffold', { exact: true }).click();
}
const scaffoldExamples = JSON.stringify({ cases: [{ name: 'positive', input: 3, output: 6 }] });

async function reviewedExistingProject(page: import('@playwright/test').Page, query = '') {
  await approvedScaffold(page, query);
  await page.getByText('New project scaffold', { exact: true }).click();
  await page.getByText('Use an existing project', { exact: true }).click();
  await page.getByLabel('Existing project source').selectOption('internal-project');
  await page.getByLabel('Existing project snapshot name').fill('internal-e2e-first');
  await page
    .getByLabel('Existing project selected files')
    .fill('app.py\ntest_acceptance.py\nrequirements.md');
  await page.getByLabel('Existing project new files').fill('helper.py');
  await page.getByRole('button', { name: 'Review project import', exact: true }).click();
}

test('existing project import reviews source and absent targets before separate registration', async ({
  page,
}) => {
  await reviewedExistingProject(page);
  const panel = page.locator('.existing-project-panel');
  const review = page.getByRole('region', { name: 'Existing project file review' });
  await expect(review).toContainText('C:/fixture/internal-project');
  await expect(review).toContainText('helper.py — new file allowed');
  await expect(
    panel.getByRole('button', { name: 'Create reviewed project snapshot', exact: true }),
  ).toBeDisabled();
  await review
    .getByLabel('I reviewed these existing and new files for this specification.')
    .check();
  await panel
    .getByRole('button', { name: 'Create reviewed project snapshot', exact: true })
    .click();
  await expect(panel.getByRole('status')).toContainText('Source unchanged');
  await expect(
    panel.getByRole('button', { name: 'Register reviewed workspace', exact: true }),
  ).toHaveCount(0);
  await panel.getByRole('button', { name: 'Review workspace registration', exact: true }).click();
  await expect(
    panel.getByRole('button', { name: 'Register reviewed workspace', exact: true }),
  ).toBeDisabled();
  await panel.getByLabel('I reviewed the workspace, source and fixed native test command.').check();
  await panel.getByRole('button', { name: 'Register reviewed workspace', exact: true }).click();
  await expect(
    panel.getByRole('heading', { name: 'Review project permissions', exact: true }),
  ).toBeVisible();
});

test('editing existing project selections clears the reviewed import and consent', async ({
  page,
}) => {
  await reviewedExistingProject(page);
  await page.getByLabel('I reviewed these existing and new files for this specification.').check();
  await page.getByLabel('Existing project new files').fill('different.py');
  await expect(page.getByRole('region', { name: 'Existing project file review' })).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Create reviewed project snapshot', exact: true }),
  ).toHaveCount(0);
});

test('uncertain project import recovers through a receipt without replay', async ({ page }) => {
  await reviewedExistingProject(page, '&importlost=1');
  const panel = page.locator('.existing-project-panel');
  await page.getByLabel('I reviewed these existing and new files for this specification.').check();
  await page.getByRole('button', { name: 'Create reviewed project snapshot', exact: true }).click();
  await expect(panel.getByRole('alert')).toContainText('outcome is uncertain');
  await expect(
    panel.getByRole('button', { name: 'Create reviewed project snapshot', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Check import receipt', exact: true }).click();
  await expect(panel.getByRole('status')).toContainText('Project snapshot ready');
});

test('existing project access stays disabled without trusted host roots', async ({ page }) => {
  await approvedScaffold(page, '&noexisting=1');
  await page.getByText('Use an existing project', { exact: true }).click();
  const panel = page.locator('.existing-project-panel');
  await expect(panel).toContainText('not configured');
  await expect(panel.getByLabel('Existing project source')).toBeDisabled();
  await expect(
    panel.getByRole('button', { name: 'Review project import', exact: true }),
  ).toBeDisabled();
});

test('TypeScript scaffold exposes reviewed tool versions and clears consent on template changes', async ({
  page,
}) => {
  await approvedScaffold(page);
  await page.getByLabel('Scaffold project template').selectOption('typescript-json-function-v1');
  await page.getByLabel('Scaffold project name').fill('typed-library');
  await page.getByLabel('Scaffold acceptance examples').fill(scaffoldExamples);
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  const review = page.getByRole('region', { name: 'Scaffold file review' });
  await expect(review).toContainText('Node SHA-256');
  await expect(review).toContainText('Version 7.0.2');
  await expect(review).toContainText('Compiler SHA-256');
  await review.getByText('src/main.ts', { exact: true }).click();
  await expect(review).toContainText('export function handle');
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  await page.getByLabel('Scaffold project template').selectOption('python-json-function-v1');
  await expect(review).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Create reviewed project', exact: true }),
  ).toHaveCount(0);
});

test('TypeScript creation stays disabled without host toolchain configuration', async ({
  page,
}) => {
  await approvedScaffold(page, '&nonode=1');
  await expect(
    page.getByRole('option', { name: 'TypeScript JSON function', exact: true }),
  ).toHaveAttribute('disabled', '');
  expect(
    await page
      .getByRole('option', { name: 'TypeScript JSON function', exact: true })
      .evaluate((element) => (element as HTMLOptionElement).disabled),
  ).toBe(true);
  await expect(page.locator('.scaffold-panel')).toContainText(
    'reviewed host Node/TypeScript toolchain',
  );
});

test('scaffold file review requires explicit consent and invalidates edited plans', async ({
  page,
}) => {
  await approvedScaffold(page);
  await page.getByLabel('Scaffold project name').fill('client-service');
  await page.getByLabel('Scaffold acceptance examples').fill(scaffoldExamples);
  await page.getByRole('button', { name: 'Check creation receipt', exact: true }).click();
  await expect(page.getByRole('status', { name: 'Scaffold creation receipt' })).toContainText(
    'No published project receipt',
  );
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  const review = page.getByRole('region', { name: 'Scaffold file review' });
  await expect(review).toContainText('C:/fixture/scaffolds/client-service');
  await expect(review.locator('details')).toHaveCount(13);
  await review.getByText('docs/02_SYSTEM_ARCHITECTURE.md', { exact: true }).click();
  await expect(review).toContainText('host_template');
  const create = page.getByRole('button', { name: 'Create reviewed project', exact: true });
  await expect(create).toBeDisabled();
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  await expect(create).toBeEnabled();
  await page.getByLabel('Scaffold project name').fill('changed-service');
  await expect(review).toHaveCount(0);
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  await expect(create).toBeDisabled();
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  await create.click();
  await expect(
    page.getByRole('heading', { name: 'Project creation receipt', exact: true }),
  ).toBeVisible();
  await expect(create).toBeDisabled();
  await expect(page.getByRole('status', { name: 'Scaffold creation receipt' })).toContainText(
    'Creation does not register this workspace',
  );
});

test('scaffold uncertain create never retries and recovers through receipt lookup', async ({
  page,
}) => {
  await approvedScaffold(page, '&scaffoldlost=1');
  await page.getByLabel('Scaffold project name').fill('uncertain-service');
  await page.getByLabel('Scaffold acceptance examples').fill(scaffoldExamples);
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  const create = page.getByRole('button', { name: 'Create reviewed project', exact: true });
  await create.click();
  await expect(page.getByRole('alert')).toContainText('outcome is uncertain');
  await expect(create).toBeDisabled();
  await expect(
    page.getByRole('button', { name: 'Preview project files', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Check creation receipt', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Project creation receipt', exact: true }),
  ).toBeVisible();
  await expect(create).toBeDisabled();
});

test('scaffold disabled host and malformed examples remain visible', async ({ page }) => {
  await approvedScaffold(page, '&noscaffold=1');
  await expect(page.locator('.scaffold-panel')).toContainText('Project creation is disabled');
  await expect(page.getByLabel('Scaffold project name')).toBeDisabled();
  await approvedScaffold(page);
  await page.getByLabel('Scaffold project name').fill('client-service');
  await page.getByLabel('Scaffold acceptance examples').fill('{invalid');
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('must be valid JSON');
  await expect(page.getByRole('region', { name: 'Scaffold file review' })).toHaveCount(0);
});

test('scaffold review fits a narrow desktop panel', async ({ page }, info) => {
  await page.setViewportSize({ width: 720, height: 900 });
  await approvedScaffold(page);
  await page.getByLabel('Scaffold project name').fill('responsive-service');
  await page.getByLabel('Scaffold acceptance examples').fill(scaffoldExamples);
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Scaffold file review' })).toBeVisible();
  const geometry = await page
    .locator('.scaffold-panel')
    .evaluate((element) => ({ width: element.clientWidth, content: element.scrollWidth }));
  expect(geometry.content).toBeLessThanOrEqual(geometry.width + 1);
  const formGeometry = await page.locator('.scaffold-panel fieldset').evaluate((element) => ({
    height: element.clientHeight,
    content: element.scrollHeight,
  }));
  expect(formGeometry.content).toBeLessThanOrEqual(formGeometry.height + 1);
  await page.screenshot({ path: info.outputPath('scaffold-review.png'), fullPage: true });
});

test('project builder reviews registration and grants before queuing model work', async ({
  page,
}, info) => {
  await approvedScaffold(page);
  await page.getByLabel('Scaffold project name').fill('integrated-site');
  await page.getByLabel('Scaffold project template').selectOption('python-web-service-v1');
  await page.getByLabel('Scaffold acceptance examples').fill(
    JSON.stringify({
      cases: [
        {
          name: 'home',
          input: { method: 'GET', path: '/', body: '' },
          output: { status: 200, content_type: 'text/html', body: '<h1>Ready</h1>' },
        },
      ],
    }),
  );
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  await expect(
    page.getByRole('region', { name: 'Scaffold file review' }).locator('details'),
  ).toHaveCount(15);
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  await page.getByRole('button', { name: 'Create reviewed project', exact: true }).click();
  const flow = page.getByRole('region', { name: 'Project build workflow' });
  await flow.getByRole('button', { name: 'Review workspace registration', exact: true }).click();
  await expect(
    flow.getByRole('button', { name: 'Register reviewed workspace', exact: true }),
  ).toBeDisabled();
  await flow.getByLabel('I reviewed the workspace, source and fixed native test command.').check();
  await flow.getByRole('button', { name: 'Register reviewed workspace', exact: true }).click();
  await expect(
    flow.getByRole('heading', { name: 'Review project permissions', exact: true }),
  ).toBeVisible();
  await expect(
    flow.getByRole('button', { name: 'Apply reviewed project permissions', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: '≋ Activity', exact: true }).click();
  await page
    .getByRole('region', { name: 'Registered project library' })
    .getByRole('button', { name: 'Open project workflow', exact: true })
    .click();
  const grantCheckbox = flow.getByLabel(
    'I reviewed the permission mode and exact resource grants.',
  );
  const geometry = await grantCheckbox.evaluate((input) => {
    const box = input.getBoundingClientRect();
    const label = input.closest('label')!.getBoundingClientRect();
    return { width: box.width, left: box.left - label.left };
  });
  expect(geometry.width).toBeLessThan(30);
  expect(Math.abs(geometry.left)).toBeLessThan(2);
  await flow.getByLabel('I reviewed the permission mode and exact resource grants.').check();
  await flow
    .getByRole('button', { name: 'Apply reviewed project permissions', exact: true })
    .click();
  await expect(
    flow.getByRole('button', { name: 'Queue model repair job', exact: true }),
  ).toBeDisabled();
  await flow.getByLabel('Allow model calls for this job', { exact: true }).check();
  await flow.getByRole('button', { name: 'Queue model repair job', exact: true }).click();
  await expect(flow.locator('.build-job-card > strong')).toContainText('queued');
  await flow.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: info.outputPath('integrated-project-builder.png'),
    fullPage: true,
  });
  await page.getByRole('button', { name: '≋ Activity', exact: true }).click();
  await page
    .getByRole('region', { name: 'Registered project library' })
    .getByRole('button', { name: 'Open project workflow', exact: true })
    .click();
  const saved = page.getByRole('region', { name: 'Saved project workflow' });
  await expect(saved.getByRole('heading', { name: 'integrated-site', exact: true })).toBeVisible();
  await expect(saved.locator('.build-job-card > strong')).toContainText('queued');
  await page.getByRole('button', { name: 'Close project workflow', exact: true }).click();
  await expect(saved).toHaveCount(0);
});

test('host-disabled native registration cannot be activated by renderer consent', async ({
  page,
}) => {
  await approvedScaffold(page, '&noregistration=1');
  await page.getByLabel('Scaffold project name').fill('disabled-execution');
  await page.getByLabel('Scaffold acceptance examples').fill(scaffoldExamples);
  await page.getByRole('button', { name: 'Preview project files', exact: true }).click();
  await page
    .getByLabel('I reviewed the destination, all files, examples and execution profile.')
    .check();
  await page.getByRole('button', { name: 'Create reviewed project', exact: true }).click();
  const flow = page.getByRole('region', { name: 'Project build workflow' });
  await expect(flow).toContainText('Native registration is host-disabled');
  await flow.getByRole('button', { name: 'Review workspace registration', exact: true }).click();
  await flow.getByLabel('I reviewed the workspace, source and fixed native test command.').check();
  await expect(
    flow.getByRole('button', { name: 'Register reviewed workspace', exact: true }),
  ).toBeDisabled();
});

test('operations inbox acknowledgement survives reload without authorizing work', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '≋ Activity' }).click();
  const inbox = page.getByRole('region', { name: 'Persistent outcome inbox' });
  await expect(inbox).toContainText('2 unread');
  await inbox.getByRole('button', { name: 'Acknowledge outcome' }).first().click();
  await expect(inbox).toContainText('1 unread');
  await expect(page.getByRole('region', { name: 'Work needing attention' })).toContainText(
    'budget limited',
  );
  await page.reload();
  await page.getByRole('button', { name: '≋ Activity' }).click();
  await expect(inbox).toContainText('1 unread');
  await expect(inbox).toContainText('Acknowledged');
  await expect(inbox).toContainText('Source delivery requires separate review');
  await inbox.getByRole('button', { name: 'Inspect tested run and delivery' }).click();
  await expect(page.getByText('Execution checkpoint', { exact: true })).toBeVisible();
});

test('operations makes host disablement and elapsed budgets visible at narrow widths', async ({
  page,
}) => {
  await page.setViewportSize({ width: 860, height: 900 });
  await page.goto('/?preview=1&runnerdisabled=1');
  await page.getByRole('button', { name: '≋ Activity' }).click();
  const panel = page.getByRole('region', { name: 'Unattended operations' });
  await expect(panel).toContainText('host-disabled');
  await expect(panel).toContainText('Deadline elapsed');
  await expect(panel).toContainText('does not confirm runner health');
  await expect(panel.getByRole('button', { name: 'Refresh operations' })).toBeEnabled();
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
    .toBe(true);
  await page.screenshot({ path: 'test-results/operations-center-narrow.png', fullPage: true });
});

test('scheduled builds require explicit time review and keep their planned time through pause', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⚒ Build jobs', exact: true }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('Repair the portal overnight');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByLabel('Schedule build start', { exact: true }).check();
  const date = new Date(Date.now() + 3600000);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 19)
    .replace(/:00$/, '');
  await page.getByLabel('Scheduled build start time', { exact: true }).fill(local);
  await expect(
    page.getByRole('button', { name: 'Queue model repair job', exact: true }),
  ).toBeDisabled();
  await page.getByLabel('Review scheduled build conditions', { exact: true }).check();
  await page.getByLabel('Scheduled build start window', { exact: true }).fill('2');
  await expect(
    page.getByLabel('Review scheduled build conditions', { exact: true }),
  ).not.toBeChecked();
  await expect(
    page.getByRole('button', { name: 'Queue model repair job', exact: true }),
  ).toBeDisabled();
  await page.getByLabel('Review scheduled build conditions', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job', exact: true }).click();
  const card = page.locator('.build-job-card');
  await expect(card.locator(':scope > strong')).toHaveText('scheduled · baseline');
  await expect(card).toContainText('0/2 model-call slots');
  const planned = await card.getByText(/Planned start:/).innerText();
  await card.getByRole('button', { name: 'Pause repair job', exact: true }).click();
  await card.getByRole('button', { name: 'Resume repair job', exact: true }).click();
  await expect(card.getByText(/Planned start:/)).toHaveText(planned);
  await card.getByRole('button', { name: 'Cancel repair job', exact: true }).click();
  await expect(card.locator(':scope > strong')).toHaveText('cancelled · baseline');
});

test('past scheduled times cannot queue and runner contact is distinct from host enablement', async ({
  page,
}) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⚒ Build jobs', exact: true }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('A scheduled repair');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByLabel('Schedule build start', { exact: true }).check();
  await page.getByLabel('Scheduled build start time', { exact: true }).fill('2020-01-01T12:00');
  await page.getByLabel('Review scheduled build conditions', { exact: true }).check();
  await expect(
    page.getByRole('button', { name: 'Queue model repair job', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: '≋ Activity', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Runner contact' })).toContainText(
    'Worker contact: recent',
  );
  await expect(page.getByRole('region', { name: 'Runner contact' })).toContainText(
    'not an OS process-health guarantee',
  );
});

test('feature mode requires fresh model consent and is recorded in the job', async ({ page }) => {
  await page.goto('/?preview=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page.getByLabel('Build goal', { exact: true }).fill('Add a project summary feature');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByLabel('Build coding mode').selectOption('feature');
  await expect(
    page.getByLabel('Allow model calls for this job', { exact: true }),
  ).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Queue model feature job' })).toBeDisabled();
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model feature job' }).click();
  await expect(page.locator('.build-job-card')).toContainText(
    'Feature · independent acceptance required',
  );
  const configuration = page.locator('.build-job-configuration');
  await expect(configuration).not.toHaveAttribute('open');
  await configuration.locator('summary').click();
  await expect(page.getByLabel('Build workspace', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Refresh build jobs', exact: true }).click();
  await expect(page.getByLabel('Build workspace', { exact: true })).toBeVisible();
});

test('retrieval mode requires fresh consent and exposes selected context evidence', async ({
  page,
}) => {
  await page.goto('/?preview=1&buildreview=1');
  await page.getByRole('button', { name: '⚒ Build jobs' }).click();
  await page
    .getByLabel('Build goal', { exact: true })
    .fill('Fix totals using approved snapshot context');
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByLabel('Build context mode').selectOption('retrieve');
  await expect(
    page.getByLabel('Allow model calls for this job', { exact: true }),
  ).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Queue model repair job' })).toBeDisabled();
  await page.getByLabel('Allow model calls for this job', { exact: true }).check();
  await page.getByRole('button', { name: 'Queue model repair job' }).click();
  await expect(page.locator('.build-job-card')).toContainText('Retrieved context');
  await page.getByRole('button', { name: 'Review job proposal' }).click();
  const evidence = page.locator('.retrieval-review');
  await evidence.locator('summary').click();
  await expect(evidence).toContainText('2 of 3 candidates');
  await expect(evidence).toContainText('large.py: context_budget');
  await expect(evidence).toContainText('tests/test_totals.py');
  await expect(evidence).toContainText('protected');
});
