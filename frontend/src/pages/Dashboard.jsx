import { AsyncPanel, Balance, PageTitle } from '../components/common.jsx'
import { query } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'

export default function Dashboard({ scope, health, navigate }) {
  const summary = useApi(query('/dataset/summary', { scope }))
  return <>
    <PageTitle title="A corpus. Two models. Clearer reasoning.">
      Explore the evidence behind email classification, from empirical counts to held-out errors.
    </PageTitle>
    <div className="columns overview">
      <section className="panel">
        <h2>The corpus at a glance</h2><p className="muted">Apache SpamAssassin Public Corpus · historical email</p>
        <AsyncPanel resource={summary}>{data => <>
          <p className="lead"><strong>{data.total.toLocaleString()}</strong> retained emails in <strong>{scope}</strong> scope</p>
          <Balance summary={data} />
          <p className="note">Observed corpus proportions describe this selection, not today’s email traffic.</p>
          <button onClick={() => navigate('/dataset')}>Explore the dataset</button>
        </>}</AsyncPanel>
      </section>
      <section className="panel readiness">
        <h2>Ready for a walkthrough?</h2>
        <AsyncPanel resource={health}>{data => <>
          <dl>{[
            ['Dataset', data.dataset_ready], ['Multinomial model', data.models_ready.multinomial],
            ['Bernoulli model', data.models_ready.bernoulli], ['Held-out evaluation', data.evaluation_ready],
          ].map(([label, ready]) => <div key={label}><dt>{label}</dt><dd className={ready ? 'ready' : 'unready'}>{ready ? 'Ready' : 'Needs preparation'}</dd></div>)}</dl>
          <p className="note">Dataset analysis stays available when models need preparation.</p>
        </>}</AsyncPanel>
        <button className="secondary" onClick={health.retry}>Check services</button>
      </section>
    </div>
    <section className="walkthrough">
      <h2>Follow the evidence</h2>
      <div className="journey">{[
        ['/probability', 'Count a word', 'Read empirical frequencies with their denominators.'],
        ['/statistics', 'Question an association', 'Check expected counts and uncertainty before concluding.'],
        ['/detect', 'Compare predictions', 'See two models reason about the same transient text.'],
        ['/evaluation', 'Inspect the errors', 'Compare false positives and missed spam on identical test IDs.'],
      ].map(([path, title, copy]) => <a key={path} href={path} onClick={event => { if (!event.ctrlKey && !event.metaKey && !event.shiftKey) { event.preventDefault(); navigate(path) } }}>
        <h3>{title}</h3><p>{copy}</p><span className="text-link">Open analysis</span>
      </a>)}</div>
    </section>
  </>
}
