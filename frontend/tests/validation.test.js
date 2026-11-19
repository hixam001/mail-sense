import assert from 'node:assert/strict'
import test from 'node:test'
import { canonicalWord, binomialInput, predictionInput } from '../src/lib/validation.js'
import { formatNumber } from '../src/lib/format.js'

test('canonical tokens normalize case and NFC without accepting arbitrary text', () => {
  assert.equal(canonicalWord(' FREE '), 'free')
  assert.equal(canonicalWord('cafe\u0301'), 'café')
  for (const value of ['', 'a', 'two words', 'free!', 'private@example.invalid', 'x'.repeat(65)]) {
    assert.equal(canonicalWord(value), null)
  }
})
test('binomial controls reject missing fractions and impossible event counts', () => {
  for (const [n, k] of [['', '0'], ['10', ''], ['1.5', '1'], ['0', '0'], ['101', '1'], ['10', '11']]) {
    assert.equal(binomialInput(n, k), false)
  }
  assert.equal(binomialInput('100', '100'), true)
  assert.equal(binomialInput('1', '0'), true)
})
test('tiny positive probabilities retain meaning and undefined values stay undefined', () => {
  assert.equal(formatNumber(null, true), 'Undefined')
  assert.notEqual(formatNumber(1e-20, true), '0.00%')
  assert.match(formatNumber(4.499e-155), /E-155/)
  assert.equal(formatNumber(.9999999, true), '>99.99%')
})

test('prediction length uses trimmed Unicode code points without truncation', () => {
  assert.equal(predictionInput(' \n ').length, 0)
  assert.ok(predictionInput('\u0000\u0001').error)
  assert.equal(predictionInput('𝒙'.repeat(50_000)).error, null)
  const long = 'x'.repeat(50_001)
  assert.equal(predictionInput(long).text, long)
  assert.ok(predictionInput(long).error)
  assert.equal(predictionInput('\u0085 mail \u001c').text, 'mail')
  assert.equal(canonicalWord('\ufefffree'), null)
})
