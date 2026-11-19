import { useState } from 'react'
import { AsyncPanel, Notes, NumberValue, PageTitle } from '../components/common.jsx'
import DataTable from '../components/DataTable.jsx'
import WordForm from '../components/WordForm.jsx'
import { query } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import { canonicalWord } from '../lib/validation.js'

function Counts({ caption, values }) {
  return <DataTable caption={caption} columns={['Class', 'Word present', 'Word absent']}
    rows={['Spam', 'Ham'].map((label, index) => [label, ...values[index].map((value, i) => <NumberValue key={i} value={value} />)])} />
}

export default function Statistics({ scope, word, setWord }) {
  const [draft, setDraft] = useState(word)
  const [alpha, setAlpha] = useState('0.05')
  const [confidence, setConfidence] = useState('0.95')
  const [submitted, setSubmitted] = useState(null)
  const validAlpha = alpha !== '' && Number.isFinite(Number(alpha)) && Number(alpha) > 0 && Number(alpha) < 1
  const validConfidence = confidence !== '' && Number(confidence) >= .8 && Number(confidence) <= .99
  const current = submitted && validAlpha && submitted.word === canonicalWord(draft) && submitted.scope === scope && submitted.alpha === Number(alpha)
  const test = useApi(current ? '/statistics/hypothesis-test' : null, current ? submitted : undefined)
  const interval = useApi(validConfidence ? query('/statistics/confidence-interval', { scope, confidence: Number(confidence) }) : null)
  function run(selected) {
    if (!validAlpha) return
    setWord(selected)
    setSubmitted({ word: selected, scope, alpha: Number(alpha) })
    if (current) test.retry()
  }
  return <>
    <PageTitle title="Statistical Inference">Separate an observed association from a justified conclusion. Selected scope: <strong>{scope}</strong>.</PageTitle>
    <section className="panel"><h2>Pearson chi-square association test</h2>
      <p>H₀: word presence and email class are independent. H₁: they are associated.</p>
      <WordForm value={draft} onChange={setDraft} onSubmit={run} buttonLabel="Run chi-square test" disabled={!validAlpha}>
        <label>Significance (α)<input type="number" min="0" max="1" step="any" value={alpha} onChange={e => setAlpha(e.target.value)} /></label>
      </WordForm>
      {!validAlpha && <p className="validation" role="alert">Use a finite significance level strictly between 0 and 1.</p>}
      {!current ? <p className="note" role="status">Choose the word, scope and significance, then run the test. Changed settings hide the earlier result.</p> :
        <AsyncPanel resource={test}>{data => <>
          <h3 className="section-gap">“{data.word}” · {data.scope} scope · α = {data.alpha}</h3>
          <div className="columns"><Counts caption="Observed email counts" values={data.observed} /><Counts caption="Expected counts under H₀" values={data.expected} /></div>
          <p className="note">Expected count = row total × column total / grand total.</p>
          <DataTable caption="Pearson test · no Yates continuity correction" columns={['Quantity', 'Value']}
            rows={[
              ['χ² = Σ (O−E)² / E', <NumberValue key="chi" value={data.chi_square} />],
              ['Degrees of freedom', data.degrees_of_freedom],
              ['p-value', <NumberValue key="p" value={data.p_value} />],
              ['Significance α', data.alpha],
              ['Every expected count ≥ 5', data.assumptions_satisfied ? 'Yes' : 'No'],
            ]} />
          <div className={`conclusion ${data.reject_null === null ? 'caution' : ''}`} role="status">
            <h3>{data.reject_null === null ? 'No automatic decision' : data.reject_null ? 'Reject H₀ at the selected significance' : 'Do not reject H₀'}</h3>
            <p>{data.reject_null === null ? 'The expected-count approximation is unsuitable or the table is degenerate. Inspect the warnings before drawing a conclusion.' : data.reject_null ? 'There is evidence of association in this selected corpus under the test assumptions.' : 'This result does not establish independence or prove H₀.'}</p>
          </div><Notes items={data.warnings} /><p className="note">{data.limitations}</p>
        </>}</AsyncPanel>}
    </section>
    <section className="panel section-gap"><h2>Wilson interval for the spam proportion</h2>
      <p className="note">The selected corpus proportion is observed. This two-sided interval illustrates uncertainty under a sampling model; it is not a modern inbox prevalence guarantee.</p>
      <label className="short-control">Confidence level<input type="number" min="0.8" max="0.99" step="any" value={confidence} onChange={e => setConfidence(e.target.value)} /></label>
      {!validConfidence ? <p className="validation" role="alert">Use a confidence level from 0.80 to 0.99.</p> :
        <AsyncPanel resource={interval}>{data => <>
          <p className="section-gap"><strong><NumberValue value={data.confidence} percent /> Wilson interval</strong> · {data.scope} scope · {data.spam_count.toLocaleString()} spam / {data.sample_size.toLocaleString()} emails</p>
          {data.lower !== null && <svg className="interval-plot" viewBox="0 0 500 90" role="img" aria-label="Wilson interval on a zero to one proportion axis; numerical bounds below">
            <line x1="20" x2="480" y1="35" y2="35" className="axis" />
            <line x1={20 + data.lower * 460} x2={20 + data.upper * 460} y1="35" y2="35" className="interval" />
            <circle cx={20 + data.point_estimate * 460} cy="35" r="5" />
            <text x="20" y="75">0%</text><text x="480" y="75" textAnchor="end">100% spam</text>
          </svg>}
          <DataTable caption="Two-sided Wilson score bounds" columns={['Quantity', 'Value']}
            rows={[
              ['Observed proportion', <NumberValue key="p" value={data.point_estimate} percent />],
              ['Lower bound', <NumberValue key="l" value={data.lower} percent />],
              ['Upper bound', <NumberValue key="u" value={data.upper} percent />],
            ]} />
          <Notes items={data.notes} /><p className="note">{data.limitations} Independence is assumed, not established.</p>
        </>}</AsyncPanel>}
    </section>
  </>
}
