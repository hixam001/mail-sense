import { AsyncPanel, Notes, NumberValue, PageTitle } from '../components/common.jsx'
import DataTable from '../components/DataTable.jsx'
import { useApi } from '../lib/useApi.js'
import { comparableEvaluation } from '../lib/evaluation.js'

const metrics = [
  ['accuracy', 'Accuracy', '(TP + TN) / all test emails'],
  ['precision', 'Precision', 'TP / (TP + FP)'],
  ['recall', 'Recall (spam detection)', 'TP / (TP + FN)'],
  ['f1', 'F1 score', '2TP / (2TP + FP + FN)'],
  ['false_positive_rate', 'False-positive rate', 'FP / (FP + TN)'],
]

function ConfusionMatrix({ name, model }) {
  const c = model.confusion_matrix
  const cell = (count, label, error) => <div className={`matrix-cell ${error ? 'matrix-error' : 'matrix-correct'}`}><strong>{count.toLocaleString()}</strong><span>{label}</span></div>
  return <section className="panel" aria-label={name}>
    <h2>{name}</h2>
    <DataTable caption="Actual rows × predicted columns · spam is positive" minWidth={350}
      columns={['Actual class', 'Predicted ham', 'Predicted spam']}
      rows={[
        ['Ham', cell(c.tn, 'TN: correct ham', false), cell(c.fp, 'FP: false alarm', true)],
        ['Spam', cell(c.fn, 'FN: missed spam', true), cell(c.tp, 'TP: detected spam', false)],
      ]} />
    <p className="note"><strong>{c.fp} false positives:</strong> legitimate emails labeled spam. <strong>{c.fn} false negatives:</strong> spam labeled ham.</p>
    <Notes items={model.notes} />
  </section>
}

export default function Evaluation({ onDetect }) {
  const report = useApi('/models/comparison')
  return <>
    <PageTitle title="Model Evaluation">Compare error profiles on identical held-out emails. The positive class is <strong>spam</strong>.</PageTitle>
    <AsyncPanel resource={report}>{data => !comparableEvaluation(data) ?
      <div className="state error" role="alert"><h2>Comparison unavailable</h2><p>Test membership or counts do not agree. Prepare and verify the matching local evaluation artifacts.</p><button onClick={report.retry}>Retry comparison</button></div> : <>
        <section className="panel"><h2>One shared test set</h2>
          <p><strong>{data.test_count.toLocaleString()} identical held-out emails</strong> · test membership verified for both models.</p>
          <p className="note">Stratified 80/20 split, seed 42. Shared training-fitted vocabulary and fixed Laplace smoothing α = 1. Test labels are used for evaluation, not fitting or tuning.</p>
          <details><summary>Inspect split and artifact identities</summary>
            <dl className="identity-list">{[
              ['Dataset ID', data.dataset_id], ['Split ID', data.split_id],
              ['Artifact generation', data.artifact_id], ['Test membership SHA-256', data.test_ids_sha256],
            ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd><code>{value}</code></dd></div>)}</dl>
          </details>
        </section>
        <section className="panel section-gap"><h2>Held-out performance</h2>
          <DataTable caption="Measured model metrics · positive class spam" minWidth={720}
            columns={['Metric', 'Multinomial', 'Bernoulli', 'Definition']}
            rows={metrics.map(([key, label, definition]) => [label,
              <NumberValue key="m" value={data.models.multinomial[key]} percent />,
              <NumberValue key="b" value={data.models.bernoulli[key]} percent />, definition])} />
          <p className="note">Accuracy alone does not describe both error types. Precision describes predicted spam; recall describes actual spam. False-positive rate uses actual ham as its denominator. Undefined denominators remain undefined.</p>
        </section>
        <div className="columns section-gap">
          <ConfusionMatrix name="Multinomial Naive Bayes" model={data.models.multinomial} />
          <ConfusionMatrix name="Bernoulli Naive Bayes" model={data.models.bernoulli} />
        </div>
        <section className="panel section-gap"><h2>What these results can tell us</h2>
          <Notes items={data.limitations} />
          <p className="note">Exact text deduplication does not remove all near duplicates. A single historical holdout does not establish performance on modern messages or independence between emails.</p>
          <button className="secondary" onClick={onDetect}>Try the models</button>
        </section>
      </>}
    </AsyncPanel>
  </>
}
