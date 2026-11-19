// Real stop/restart and missing-model checks use only a temporary private artifact copy.
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { createHash } from 'node:crypto'
import { chmod, copyFile, mkdir, mkdtemp, readFile, rm, unlink, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright-core'

const root = fileURLToPath(new URL('../../', import.meta.url)), api = 'http://127.0.0.1:8000/api/v1', ui = 'http://localhost:5173'
const stage = await mkdtemp(join(tmpdir(), 'mailsense-release-'))
await chmod(stage, 0o700)
const files = [
  ...['source_manifest.json', 'messages.parsed.jsonl', 'parsing_report.json', 'messages.csv', 'deduplication_report.json', 'split_manifest.json'].map(name => `data/processed/${name}`),
  ...['vectorizer.joblib', 'multinomial.joblib', 'bernoulli.joblib', 'metadata.json'].map(name => `artifacts/models/${name}`),
  'artifacts/reports/evaluation.json',
]
let server, browser
let logs = ''
const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
async function stop() {
  if (!server || server.exitCode !== null || server.signalCode !== null) return
  const ended = new Promise(resolve => server.once('exit', resolve))
  server.kill('SIGTERM')
  await ended
}
async function start() {
  server = spawn(join(root, 'backend/.venv/bin/python'), ['backend/tests/fixture_api.py', stage], {
    cwd: root, env: { ...process.env, PYTHONPATH: join(root, 'backend') }, stdio: ['ignore', 'pipe', 'pipe'],
  })
  server.stdout.on('data', data => { logs += data.toString() })
  server.stderr.on('data', data => { logs += data.toString() })
  for (let i = 0; i < 100; i++) {
    if (server.exitCode !== null) throw new Error('Staging API exited before readiness.')
    try { if ((await fetch(api + '/health')).ok) return } catch { /* wait for owned process */ }
    await wait(100)
  }
  throw new Error('Staging API did not start.')
}
const digest = async () => Object.fromEntries(await Promise.all(files.map(async file => [file,
  createHash('sha256').update(await readFile(join(stage, file))).digest('hex')])) )

try {
  files.push(...JSON.parse(await readFile(join(root, 'data/processed/source_manifest.json'), 'utf8')).archives.map(a => `data/raw/${a.archive_name}`))
  let occupied = false
  try { await fetch(api + '/health'); occupied = true } catch { /* must own failure-test API */ }
  assert.equal(occupied, false, 'Stop any existing API before the controlled failure test.')
  for (const file of files) {
    await mkdir(resolve(stage, file, '..'), { recursive: true, mode: 0o700 })
    await copyFile(join(root, file), join(stage, file))
    await chmod(join(stage, file), 0o600)
  }
  const original = await digest()
  await start()
  const health = await (await fetch(api + '/health')).json()
  assert.equal(health.status, 'ready')
  browser = await chromium.launch({ ...(process.env.MAILSENSE_BROWSER ? { executablePath: process.env.MAILSENSE_BROWSER } : {}), headless: true })
  const page = await browser.newPage()
  page.setDefaultTimeout(15_000)
  const errors = []; page.on('pageerror', error => errors.push(error.message))
  await page.goto(ui + '/detect')
  await page.getByLabel('Email subject and body').fill('Synthetic release test dummyrelease@example.invalid project meeting')
  await page.getByRole('button', { name: 'Classify with both models' }).click()
  await page.locator('.model-result').first().waitFor()
  assert.equal(await page.locator('.model-result').count(), 2)
  for (const text of ['', ' \n ', 'x'.repeat(50_001)]) {
    const response = await page.request.post(api + '/predict', { data: { text } })
    assert.equal(response.status(), 422)
    assert.ok(!(await response.text()).includes('x'.repeat(50)))
  }
  const maximum = await page.request.post(api + '/predict', { data: { text: 'x'.repeat(50_000) } })
  assert.equal(maximum.status(), 200)
  assert.equal((await maximum.json()).input.character_count, 50_000)
  assert.deepEqual(await digest(), original)
  assert.ok(!logs.includes('dummyrelease'))
  console.log('T07: valid/blank/overlimit/maximum HTTP and UI; staged artifacts unchanged: PASS')

  await stop()
  await page.evaluate(() => window.dispatchEvent(new Event('focus')))
  await page.getByLabel('Email subject and body').fill('Synthetic retry after actual API shutdown')
  await page.getByRole('button', { name: 'Classify with both models' }).click()
  await page.getByRole('heading', { name: 'Analysis unavailable' }).waitFor()
  assert.equal(await page.locator('.model-result').count(), 0)
  await page.getByText('API unavailable', { exact: true }).waitFor()
  await start()
  await page.evaluate(() => window.dispatchEvent(new Event('focus')))
  await page.getByRole('button', { name: 'Retry analysis' }).click()
  await page.locator('.model-result').first().waitFor()

  const modelFile = join(stage, 'artifacts/models/bernoulli.joblib')
  const modelBytes = await readFile(modelFile)
  await unlink(modelFile)
  const degraded = await (await fetch(api + '/health')).json()
  assert.equal(degraded.dataset_ready, true)
  assert.equal(degraded.status, 'degraded')
  assert.equal(degraded.models_ready.bernoulli, false)
  await page.goto(ui + '/dataset')
  await page.getByText('Corpus composition', { exact: true }).waitFor()
  await page.getByText('Descriptive statistics', { exact: true }).waitFor()
  await page.getByText('Top 15 words', { exact: false }).waitFor()
  await page.locator('nav a[href="/detect"]').click()
  await page.getByRole('button', { name: 'Load synthetic example' }).click()
  await page.getByRole('button', { name: 'Classify with both models' }).click()
  await page.getByRole('heading', { name: 'Analysis unavailable' }).waitFor()
  assert.equal(await page.locator('.model-result').count(), 0)
  await writeFile(modelFile, modelBytes, { mode: 0o600 })
  await page.getByRole('button', { name: 'Retry analysis' }).click()
  await page.locator('.model-result').first().waitFor()
  assert.equal((await (await fetch(api + '/health')).json()).status, 'ready')
  assert.deepEqual(await digest(), original)
  assert.deepEqual(errors, [])
  console.log('T08: actual API stop/restart, missing model with working analytics, safe retry/restoration: PASS')
  await mkdir(join(root, 'frontend/test-results'), { recursive: true })
  await writeFile(join(root, 'frontend/test-results/release-browser.json'), JSON.stringify({
    checked_at: new Date().toISOString(), browser: browser.version(), T07: 'pass', T08: 'pass',
    dataset_ready_without_models: true, staged_artifact_bytes_unchanged: true,
    input_absent_from_server_logs: true, split_id: health.split_id,
  }, null, 2) + '\n')
} finally {
  if (browser) await browser.close()
  await stop()
  await rm(stage, { recursive: true, force: true })
}
