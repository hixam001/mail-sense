import { useState } from 'react'
import { AsyncPanel, Notes, NumberValue, PageTitle } from '../components/common.jsx'
import DataTable from '../components/DataTable.jsx'
import WordForm from '../components/WordForm.jsx'
import { query } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import { binomialInput, canonicalWord } from '../lib/validation.js'

const fractions = [
  ['p_spam', 'P(spam)', 'Prior: spam emails / all selected emails'],
  ['p_word', 'P(word)', 'Emails containing word / all selected emails'],
  ['p_spam_and_word', 'P(spam ∩ word)', 'Spam emails containing word / all selected emails'],
  ['p_word_given_spam', 'P(word | spam)', 'Spam emails containing word / spam emails'],
  ['p_spam_given_word', 'P(spam | word)', 'Posterior: spam emails containing word / emails containing word'],
]

export default function Probability({ scope, word, setWord, onInference }) {
  const [draft, setDraft] = useState(word)
  const [trials, setTrials] = useState('10')
  const [successes, setSuccesses] = useState('1')
  const current = canonicalWord(draft) === word
  const validBinomial = binomialInput(trials, successes)
  const probability = useApi(current ? query('/probability/word', { scope, word }) : null)
  const distribution = useApi(current && validBinomial ? query('/probability/distributions', {
    scope, word, trials: Number(trials), successes: Number(successes),
  }) : null)
  return <>
    <PageTitle title="Probability Analysis">Count first, then calculate. These are empirical document frequencies, with no smoothing.</PageTitle>
    <section className="panel"><h2>Choose a word</h2>
      <WordForm value={draft} onChange={setDraft} onSubmit={setWord} />
      {!current && <p className="note" role="status">Submit the new word to update the analysis.</p>}
    </section>
    {current && <>
      <section className="panel section-gap"><h2>Word “{word}” · {scope} scope</h2>
        <AsyncPanel resource={probability}>{data => <>
          <DataTable caption={`Observed contingency counts · ${data.total.toLocaleString()} emails`} columns={['Class', 'Word present', 'Word absent', 'Total']}
            rows={[
              ['Spam', data.counts.spam_present, data.counts.spam_absent, data.counts.spam_present + data.counts.spam_absent],
              ['Ham', data.counts.ham_present, data.counts.ham_absent, data.counts.ham_present + data.counts.ham_absent],
              ['Total', data.counts.spam_present + data.counts.ham_present, data.counts.spam_absent + data.counts.ham_absent, data.total],
            ]} />
          <Notes items={data.notes} />
          <DataTable minWidth={800} caption="Empirical probabilities · count / denominator" columns={['Probability', 'Observed fraction', 'Value', 'Meaning']}
            rows={fractions.map(([key, label, meaning]) => [label,
              `${data.probabilities[key].numerator} / ${data.probabilities[key].denominator}`,
              <NumberValue key={key} value={data.probabilities[key].value} percent />, meaning])} />
          <div className="formula"><strong>Bayes’ rule</strong><p>P(spam | word) = P(word | spam) × P(spam) / P(word)</p>
            <p>{data.probabilities.p_word.value === 0 ? 'P(word) = 0: the empirical posterior is undefined, not 0% spam.' :
              <>For “{word}”, P(spam | word) = {data.probabilities.p_spam_given_word.numerator} / {data.probabilities.p_spam_given_word.denominator} = <NumberValue value={data.probabilities.p_spam_given_word.value} percent />.</>}</p>
          </div>
          <button className="secondary" onClick={onInference}>Test association for “{word}”</button>
        </>}</AsyncPanel>
      </section>
      <section className="panel section-gap"><h2>From one email to repeated trials</h2>
        <p className="note">A success means the word appears in an email, regardless of its spam/ham label. The observed P(word) supplies p.</p>
        <div className="filter-bar">
          <label>Trials (n)<input type="number" min="1" max="100" step="1" value={trials} onChange={e => setTrials(e.target.value)} /></label>
          <label>Successes (k)<input type="number" min="0" max={trials || 100} step="1" value={successes} onChange={e => setSuccesses(e.target.value)} /></label>
        </div>
        {!validBinomial ? <p className="validation" role="alert">Use integer n from 1 to 100 and k from 0 to n.</p> :
          <AsyncPanel resource={distribution}>{data => <>
            <h3 className="section-gap">Bernoulli: a single trial</h3>
            <DataTable caption={`Word “${data.word}” · ${data.scope} scope`} columns={['Outcome', 'Probability']}
              rows={[
                ['Absent (X = 0)', <NumberValue key="zero" value={data.bernoulli.p_zero} percent />],
                ['Present (X = 1)', <NumberValue key="one" value={data.bernoulli.p_one} percent />],
                ['Mean = p', <NumberValue key="mean" value={data.bernoulli.mean} />],
                ['Variance = p(1−p)', <NumberValue key="variance" value={data.bernoulli.variance} />],
              ]} />
            <div className="formula"><h3>Binomial: exactly k successes in n trials</h3>
              <p>P(X = k) = C(n,k) pᵏ (1−p)ⁿ⁻ᵏ</p>
              <p>n = {data.trials}, k = {data.successes}, p = <NumberValue value={data.bernoulli_p} /></p>
              <p>Probability of exactly {data.successes} occurrences in {data.trials} emails: <strong><NumberValue value={data.binomial_pmf} percent /></strong></p>
            </div><Notes items={[...data.assumptions, ...data.notes]} />
          </>}</AsyncPanel>}
      </section>
    </>}
  </>
}
