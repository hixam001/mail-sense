import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { chromium } from 'playwright-core'

const browser = await chromium.launch({ ...(process.env.MAILSENSE_BROWSER ? { executablePath: process.env.MAILSENSE_BROWSER } : {}), headless: true })
const page = await browser.newPage()
page.setDefaultTimeout(15_000)
const foreign = [], errors = [], urls = []
page.on('pageerror', error => errors.push(error.message))
page.on('request', request => urls.push(request.url()))
await page.route('**/*', route => {
  if (['localhost', '127.0.0.1', '[::1]'].includes(new URL(route.request().url()).hostname)) return route.continue()
  foreign.push(route.request().url())
  return route.abort()
})
try {
  const paths = [
    ['/', 'The corpus at a glance'], ['/dataset', 'Words that occur most often'],
    ['/probability', 'Empirical probabilities · count / denominator'],
    ['/statistics', 'Two-sided Wilson score bounds'], ['/evaluation', 'Held-out performance'],
  ]
  for (const [path, text] of paths) {
    await page.goto('http://localhost:5173' + path)
    await page.getByText(text, { exact: true }).waitFor()
    if (path === '/') await page.getByRole('button', { name: 'Explore the dataset' }).waitFor()
    if (path === '/dataset') {
      await page.getByText('tokens/email · all scope', { exact: true }).waitFor()
      await page.getByText(/^Top 15 words/).waitFor()
      await page.locator('.recharts-bar').waitFor()
    }
  }
  await page.goto('http://localhost:5173/detect')
  const text = 'Synthetic privacy test dummyprivacy@example.invalid <img src="https://dummy.invalid/never-fetch"> project meeting'
  await page.getByLabel('Email subject and body').fill(text)
  await page.getByRole('button', { name: 'Classify with both models' }).click()
  await page.locator('.model-result').first().waitFor()
  assert.equal(await page.locator('.model-result').count(), 2)
  assert.equal(await page.locator('img').count(), 0)
  assert.ok(urls.every(url => !url.includes('dummyprivacy')))
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  const policy = await (await page.request.get('http://127.0.0.1:8000/test/network-policy')).json()
  assert.deepEqual(policy, { internet_denied: true, blocked_probe: 1, runtime_denials: 0 })
  assert.deepEqual(foreign, [])
  assert.deepEqual(errors, [])
  const out = new URL('../test-results/', import.meta.url)
  await mkdir(out, { recursive: true })
  await writeFile(new URL('offline.json', out), JSON.stringify({
    checked_at: new Date().toISOString(), browser: browser.version(), result: 'pass',
    core_routes: 6, foreign_attempts: foreign.length, browser_storage_entries: 0,
    html_resources_executed: false, api_network_guard: policy,
    policy: 'Browser intercepts deny non-loopback; API Python socket guard denies internet. Not an OS network namespace.',
  }, null, 2) + '\n')
  console.log('All core routes and dual inference work under browser/API internet denial; no remote resource execution or persistent text: PASS')
} finally {
  await browser.close()
}
