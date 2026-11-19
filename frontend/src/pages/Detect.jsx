import { useState } from 'react'
import { AsyncPanel, Notes, NumberValue, PageTitle } from '../components/common.jsx'
import DataTable from '../components/DataTable.jsx'
import { query } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import { predictionInput } from '../lib/validation.js'

const modelLabels = { multinomial: 'Multinomial Naive Bayes', bernoulli: 'Bernoulli Naive Bayes' }
const example = 'Subject: Project meeting\nHello team, please review the project notes before our meeting tomorrow. Thank you.'

function ModelResult({ name, result, onToken }) {
  return <section className="panel model-result" aria-label={modelLabels[name]}>
    <h2>{modelLabels[name]}</h2>
    <p className={`prediction-label ${result.prediction === 'spam' ? 'unready' : 'ready'}`}>
      Prediction: <strong>{result.prediction === 'spam' ? 'Spam' : 'Ham (legitimate)'}</strong>
    </p>
    <p>Model-estimated P(spam): <strong><NumberValue value={result.spam_probability} percent /></strong></p>
    <p className="note">{name === 'bernoulli' ? 'Uses binary word presence and the absence of every other fitted feature.' : 'Repeated recognized tokens contribute repeatedly to the score.'}</p>
    <details><summary>Inspect log-odds contributions</summary>
      <p className="note">Positive contributions favor spam; negative contributions favor ham. These are signed log odds, not probabilities or causal explanations.</p>
      {result.top_contributions.length ? <DataTable caption="Strongest present-token contributions (up to 10)" columns={['Token', 'Log-odds contribution', 'Direction']}
        rows={result.top_contributions.map(term => [<button key={term.token} className="link-button" onClick={() => onToken(name, term.token)}>{term.token}</button>,
          <NumberValue key="contribution" value={term.log_odds_contribution} />, term.direction])} /> : <p>No known tokens to explain.</p>}
      <DataTable caption="Full score components" columns={['Component', 'Log odds']}
        rows={[
          ['Class prior', <NumberValue key="prior" value={result.class_prior_log_odds} />],
          ['Other present-token contributions', <NumberValue key="other" value={result.other_present_log_odds} />],
          ['All absent-feature contributions', <NumberValue key="absence" value={result.absence_log_odds_contribution} />],
          ['Full posterior log odds', <NumberValue key="full" value={result.log_odds} />],
        ]} />
      <p className="note">Full log odds = prior + all displayed present-token contributions + other present terms + absent-feature aggregate. Bernoulli absence terms included: {result.absence_terms_included ? 'yes' : 'no'}.</p>
    </details>
  </section>
}

function TokenDetails({ selection }) {
  const resource = useApi(query('/models/explanations', selection))
  return <section className="panel section-gap"><h2>Vocabulary weight: “{selection.word}”</h2>
    <AsyncPanel resource={resource}>{data => <>
      <p>{modelLabels[data.model]} · {data.in_vocabulary ? 'In fitted vocabulary' : 'Outside fitted vocabulary'}</p>
      <DataTable caption="General token weight · one occurrence/presence" columns={['Condition', 'Log-odds weight']}
        rows={[
          ['Word present', <NumberValue key="present" value={data.log_odds_when_present} />],
          ...(data.absence_terms_included ? [['Word absent', <NumberValue key="absent" value={data.log_odds_when_absent} />]] : []),
        ]} />
      <p className="note">{data.interpretation} Per-email effects depend on all the other features and the class prior.</p>
    </>}</AsyncPanel>
  </section>
}

export default function Detect({ onEvaluation }) {
  const [text, setText] = useState('')
  const [submitted, setSubmitted] = useState(null)
  const [selection, setSelection] = useState(null)
  const input = predictionInput(text)
  const current = submitted !== null && submitted === input.text && !input.error
  const prediction = useApi(current ? '/predict' : null, current ? { text: submitted } : undefined)
  function change(value) {
    setText(value)
    setSubmitted(null)
    setSelection(null)
  }
  function submit(event) {
    event.preventDefault()
    if (input.error || prediction.loading) return
    setSubmitted(input.text)
    if (current) prediction.retry()
  }
  return <>
    <PageTitle title="Spam Detector">Compare two frozen training models on the same text. Processing stays on this computer.</PageTitle>
    <section className="panel">
      <form onSubmit={submit}>
        <label htmlFor="email-text">Email subject and body</label>
        <textarea id="email-text" value={text} onChange={e => change(e.target.value)} rows="8"
          autoComplete="off" spellCheck="false" aria-describedby="email-help email-count" aria-invalid={Boolean(text && input.error)}
          placeholder="Paste plain text here, or load the labeled synthetic example." />
        <div className="input-meta"><p id="email-count" className="note">{input.length.toLocaleString()} / 50,000 trimmed characters</p>
          <p className="note">No saved prediction history</p></div>
        <p id="email-help" className={text && input.error ? 'validation' : 'note'}>{input.error || 'Text is held only in this page and sent to the local API for this request. Clear it or leave the page to discard it.'}</p>
        <div className="form-row">
          <button type="submit" disabled={Boolean(input.error) || prediction.loading}>{prediction.loading ? 'Classifying…' : 'Classify with both models'}</button>
          <button type="button" className="secondary" onClick={() => change('')}>Clear text and results</button>
          <button type="button" className="link-button" onClick={() => change(example)}>Load synthetic example</button>
        </div>
      </form>
    </section>
    {current && <AsyncPanel resource={prediction}>{data => <>
      <div className={`conclusion ${data.agreement ? '' : 'caution'}`} role="status">
        <h2>{data.agreement ? 'Both models agree' : 'The models disagree'}</h2>
        <p>{data.input.character_count.toLocaleString()} trimmed characters · {data.input.recognized_token_count.toLocaleString()} recognized token occurrences. Estimates depend on the training corpus and model assumptions.</p>
      </div>
      <Notes items={data.warnings} />
      <div className="columns">{Object.entries(data.models).map(([name, result]) => <ModelResult key={name} name={name} result={result} onToken={(model, word) => setSelection({ model, word })} />)}</div>
      {selection && <TokenDetails key={`${selection.model}:${selection.word}`} selection={selection} />}
      <button className="secondary section-gap" onClick={onEvaluation}>Evaluation details</button>
    </>}</AsyncPanel>}
  </>
}
