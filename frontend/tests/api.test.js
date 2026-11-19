import assert from 'node:assert/strict'
import test from 'node:test'
import { apiFetch, query } from '../src/lib/api.js'

test('only approved endpoints on the fixed local origin can be requested', async t => {
  const calls = []
  t.mock.method(globalThis, 'fetch', async (...args) => {
    calls.push(args)
    return { ok: true, json: async () => ({ status: 'ready' }) }
  })
  for (const path of ['https://foreign.invalid', '//foreign.invalid', '/../../escape', '/health#fragment']) {
    await assert.rejects(apiFetch(path), /Unsupported local request/)
  }
  assert.equal(calls.length, 0)
  await apiFetch('/health')
  assert.equal(calls[0][0], 'http://127.0.0.1:8000/api/v1/health')
  assert.equal(calls[0][1].credentials, 'omit')
  assert.equal(calls[0][1].redirect, 'error')
  assert.equal(calls[0][1].cache, 'no-store')
})

test('text is transmitted only in a JSON POST body', async t => {
  const text = 'dummysecret@example.invalid'
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.ok(!url.includes(text))
    assert.equal(options.method, 'POST')
    assert.deepEqual(JSON.parse(options.body), { text })
    return { ok: true, json: async () => ({ agreement: true }) }
  })
  assert.deepEqual(await apiFetch('/predict', { body: { text } }), { agreement: true })
})

test('query values are encoded and safe server failures are surfaced', async t => {
  assert.equal(query('/probability/word', { word: 'two words', scope: 'test' }),
    '/probability/word?word=two+words&scope=test')
  t.mock.method(globalThis, 'fetch', async () => ({
    ok: false, json: async () => ({ error: { message: 'Prepare both local models first.' } }),
  }))
  await assert.rejects(apiFetch('/predict', { body: { text: 'example' } }), /Prepare both local/)
})
