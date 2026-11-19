import assert from 'node:assert/strict'
import test from 'node:test'
import { comparableEvaluation } from '../src/lib/evaluation.js'

function fixture() {
  return {
    same_test_ids: true, test_count: 10, split_id: 'shared-split', test_ids_sha256: 'same-test-ids',
    models: Object.fromEntries(['multinomial', 'bernoulli'].map(name => [name, {
      model: name, positive_class: 'spam', test_count: 10, split_id: 'shared-split', test_ids_sha256: 'same-test-ids',
      confusion_matrix: { tn: 5, fp: 1, fn: 1, tp: 3 },
    }])),
  }
}
test('comparison requires identical membership and consistent confusion totals', () => {
  assert.equal(comparableEvaluation(fixture()), true)
  for (const mutate of [
    d => { d.same_test_ids = false }, d => { d.models.bernoulli.split_id = 'different' },
    d => { d.models.bernoulli.test_ids_sha256 = 'different' }, d => { d.models.multinomial.confusion_matrix.tp = 4 },
    d => { d.models.multinomial.confusion_matrix.fp = -1 }, d => { delete d.models.bernoulli },
  ]) {
    const data = fixture(); mutate(data)
    assert.equal(comparableEvaluation(data), false)
  }
  assert.equal(comparableEvaluation(null), false)
})
