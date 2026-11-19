import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { chromium } from 'playwright-core'
import { formatNumber } from '../src/lib/format.js'
import { textContrast } from './contrast.mjs'

const base = 'http://localhost:5173'
const api = 'http://127.0.0.1:8000/api/v1'
const out = 'test-results/ui'
const browser = await chromium.launch({
  headless: true,
  ...(process.env.MAILSENSE_BROWSER ? { executablePath: process.env.MAILSENSE_BROWSER } : {}),
})
let page = await browser.newPage({ reducedMotion: 'reduce' })
const errors = [], urls = []
const contrasts = []
function observe(target) {
  target.setDefaultTimeout(12_000)
  target.on('pageerror', error => errors.push(error.message))
  target.on('request', request => urls.push(request.url()))
}
observe(page)
const json = async path => {
  const response = await page.request.get(api + path)
  assert.equal(response.status(), 200, path)
  return response.json()
}
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))
async function fulfill(route, options) {
  try { await route.fulfill(options) } catch (error) {
    if (!error.message.includes('Route is already handled')) throw error
  }
}

try {
  const summary = await json('/dataset/summary')
  const testSummary = await json('/dataset/summary?scope=test')
  const comparison = await json('/models/comparison')
  const routes = ['/', '/dataset', '/probability', '/statistics', '/detect', '/evaluation']
  await mkdir(out, { recursive: true })
  for (const width of [1366, 390]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 900 })
    for (const route of routes) {
      await page.goto(base + route)
      await page.locator('main h1').waitFor()
      if (route === '/' || route === '/dataset') await page.getByText(summary.total.toLocaleString(), { exact: true }).first().waitFor()
      if (route === '/dataset') await page.getByText(`Top 15 words · ${summary.total.toLocaleString()} emails`, { exact: true }).waitFor()
      if (route === '/probability') await page.getByText('Empirical probabilities · count / denominator', { exact: true }).waitFor()
      if (route === '/statistics') {
        await page.getByRole('button', { name: 'Run chi-square test' }).click()
        await page.getByText('Pearson test · no Yates continuity correction', { exact: true }).waitFor()
        await page.getByText('Two-sided Wilson score bounds', { exact: true }).waitFor()
      }
      if (route === '/detect') {
        assert.equal(await page.getByLabel('Analysis source').inputValue(), 'Frozen training models')
        await page.getByRole('button', { name: 'Load synthetic example' }).click()
        await page.getByRole('button', { name: 'Classify with both models' }).click()
        await page.locator('.model-result').first().waitFor()
      }
      if (route === '/evaluation') {
        assert.equal(await page.getByLabel('Analysis source').inputValue(), 'Held-out test set')
        await page.getByText('Measured model metrics · positive class spam', { exact: true }).waitFor()
        for (const [metric, label] of [['accuracy', 'Accuracy'], ['precision', 'Precision'], ['recall', 'Recall (spam detection)'], ['f1', 'F1 score'], ['false_positive_rate', 'False-positive rate']]) {
          const row = page.getByRole('row').filter({ has: page.getByRole('rowheader', { name: label, exact: true }) })
          const text = await row.innerText()
          for (const name of ['multinomial', 'bernoulli']) assert.ok(text.includes(formatNumber(comparison.models[name][metric], true)))
        }
        if (width === 390) {
          for (const table of await page.locator('.comparison-table .table-scroll, .matrix-table .table-scroll').all()) {
            assert.ok(await table.evaluate(element => element.scrollWidth <= element.clientWidth))
          }
        }
      }
      await page.evaluate(() => window.scrollTo(0, 0))
      await wait(100)
      assert.equal(await page.locator('main h1').count(), 1)
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Page overflow: ${route} at ${width}`)
      if (width === 390) {
        const active = await page.locator('nav a[aria-current]').boundingBox()
        assert.ok(active.x >= 0 && active.x + active.width <= width, `Active mobile route hidden: ${route}`)
      }
      const contrast = await page.evaluate(textContrast)
      assert.deepEqual(contrast.failures, [], `Text contrast: ${route} at ${width}`)
      contrasts.push({ route, width, samples: contrast.samples, minimum: contrast.minimum })
      await page.screenshot({ path: `${out}/${width}-${route.slice(1) || 'overview'}.png`, fullPage: true })
    }
    if (width === 1366) {
      await page.setViewportSize({ width: 390, height: 844 })
      await wait(100)
      const active = await page.locator('nav a[aria-current]').boundingBox()
      assert.ok(active.x >= 0 && active.x + active.width <= 390, 'Active route remains visible after viewport resize')
    }
  }
  console.log('Six routes: desktop/mobile, real data, fixed sources and active navigation: PASS')

  await page.goto(base + '/detect')
  await page.getByLabel('Email subject and body').waitFor()
  await page.getByRole('link', { name: 'Skip to analysis' }).focus()
  await page.keyboard.press('Enter')
  assert.equal(await page.evaluate(() => document.activeElement.id), 'main-content')
  await page.keyboard.press('Tab')
  assert.equal(await page.evaluate(() => document.activeElement.id), 'email-text')
  await page.keyboard.insertText('Synthetic keyboard example: project meeting tomorrow')
  await page.keyboard.press('Tab')
  assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Classify with both models')
  assert.ok(await page.getByRole('button', { name: 'Classify with both models' }).evaluate(element => getComputedStyle(element).outlineStyle !== 'none'))
  await page.keyboard.press('Enter')
  await page.locator('.model-result').first().waitFor()
  assert.match(await page.evaluate(() => document.activeElement.textContent), /Both models agree|The models disagree/)
  console.log('Keyboard skip, form order, submit and visible focus: PASS')

  await page.route('**/api/v1/probability/word*', async route => {
    const response = await route.fetch()
    if (new URL(route.request().url()).searchParams.get('word') === 'free') await wait(500)
    await fulfill(route, { response })
  })
  await page.goto(base + '/probability')
  await page.getByLabel('Word to analyze').fill('offer')
  await page.getByRole('button', { name: 'Analyze word' }).click()
  await page.getByRole('heading', { name: 'Word “offer” · all scope', exact: true }).waitFor()
  await page.getByText('Empirical probabilities · count / denominator', { exact: true }).waitFor()
  await wait(600)
  assert.equal(await page.getByRole('heading', { name: 'Word “free” · all scope', exact: true }).count(), 0)
  await page.unrouteAll({ behavior: 'wait' })
  await page.getByLabel('Dataset scope').selectOption('test')
  await page.getByText(`Observed contingency counts · ${testSummary.total.toLocaleString()} emails`, { exact: true }).waitFor()
  await page.getByLabel('Word to analyze').fill('novocabularyzzxy')
  await page.getByRole('button', { name: 'Analyze word' }).click()
  await page.getByText('P(word) = 0: the empirical posterior is undefined, not 0% spam.', { exact: true }).waitFor()
  console.log('Delayed word response isolation, scope and undefined posterior: PASS')

  let predictionRequests = 0
  await page.route('**/api/v1/predict', async route => {
    predictionRequests++
    const response = await route.fetch()
    await wait(500)
    await fulfill(route, { response })
  })
  await page.goto(base + '/detect')
  await page.getByLabel('Email subject and body').fill('Synthetic transient test dummyprivate@example.invalid')
  await page.getByRole('button', { name: 'Classify with both models' }).evaluate(button => { for (let i = 0; i < 5; i++) button.click() })
  await page.getByRole('button', { name: 'Classifying…' }).waitFor()
  await page.getByLabel('Email subject and body').fill('Changed before response')
  await wait(700)
  assert.equal(predictionRequests, 1)
  assert.equal(await page.locator('.model-result').count(), 0)
  assert.ok(urls.every(url => !url.includes('dummyprivate')))
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  await page.unrouteAll({ behavior: 'wait' })
  await page.reload()
  assert.equal(await page.getByLabel('Email subject and body').inputValue(), '')
  console.log('Duplicate submit, delayed prediction discard and transient text privacy: PASS')

  await page.route('**/api/v1/dataset/distributions*', async route => {
    const response = await route.fetch()
    const data = await response.json()
    await fulfill(route, { json: { ...data, selected_records: 0, items: [], bins: [], boxplot: null } })
  })
  await page.goto(base + '/dataset')
  await page.getByText('No token occurrences in this selection.', { exact: true }).waitFor()
  await page.getByText('No observations in this selection.', { exact: true }).waitFor()
  await page.unrouteAll({ behavior: 'wait' })
  console.log('Empty chart and word-frequency responses: PASS')

  // Isolate the outage fixture from prior delayed/empty response interception.
  await page.close()
  page = await browser.newPage({ reducedMotion: 'reduce', viewport: { width: 390, height: 844 } })
  observe(page)
  await page.route('**/api/v1/dataset/summary*', route => route.abort())
  await page.goto(base)
  await page.getByRole('heading', { name: 'Analysis unavailable' }).waitFor()
  assert.equal(await page.getByText(summary.total.toLocaleString(), { exact: true }).count(), 0)
  await page.unroute('**/api/v1/dataset/summary*')
  await page.getByRole('button', { name: 'Retry analysis' }).click()
  await page.getByText(summary.total.toLocaleString(), { exact: true }).waitFor()
  await page.goto(base + '/missing')
  await page.getByRole('heading', { name: 'Page not found' }).waitFor()
  assert.ok(urls.every(url => ['localhost', '127.0.0.1', '[::1]'].includes(new URL(url).hostname)))
  assert.deepEqual(errors, [])
  const evidence = { checked_at: new Date().toISOString(), browser: browser.version(), routes: 6,
    viewports: ['1366x900', '390x844'], checks: ['routes', 'keyboard', 'stale responses', 'privacy', 'retry', '404'],
    dataset_id: summary.dataset_id, split_id: summary.split_id, text_contrast: contrasts, result: 'pass' }
  await writeFile(`${out}/evidence.json`, JSON.stringify(evidence, null, 2) + '\n')
  console.log('Network recovery, local-only requests, 404 and browser exceptions: PASS')
} catch (error) {
  await page.screenshot({ path: `${out}/failure.png`, fullPage: true }).catch(() => {})
  console.error('Browser diagnostics:', JSON.stringify({ path: new URL(page.url()).pathname,
    errors, headings: await page.locator('h1,h2').allTextContents(),
    recent_requests: urls.slice(-12) }))
  throw error
} finally {
  await browser.close()
}
