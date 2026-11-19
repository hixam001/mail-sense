import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AsyncPanel, Balance, Notes, NumberValue, PageTitle } from '../components/common.jsx'
import DataTable from '../components/DataTable.jsx'
import BoxPlot from '../components/BoxPlot.jsx'
import { query } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'

const labels = { all: 'All emails', ham: 'Ham (legitimate)', spam: 'Spam' }
const metrics = [
  ['n', 'Emails (n)'], ['mean', 'Mean'], ['median', 'Median'], ['mode', 'Mode'],
  ['min', 'Minimum'], ['q1', 'First quartile (Q1)'], ['q3', 'Third quartile (Q3)'],
  ['max', 'Maximum'], ['iqr', 'Interquartile range'], ['sample_variance', 'Sample variance'],
  ['sample_std', 'Sample standard deviation'],
]
const compact = value => Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(value)

export default function Dataset({ scope, onWord }) {
  const [metric, setMetric] = useState('token_count')
  const [classLabel, setClassLabel] = useState('all')
  const summary = useApi(query('/dataset/summary', { scope }))
  const statistics = useApi(query('/dataset/statistics', { scope, metric }))
  const distribution = useApi(query('/dataset/distributions', { scope, metric, class_label: classLabel }))
  const words = useApi(query('/dataset/distributions', { scope, metric: 'top_words', class_label: classLabel, top_n: 15 }))
  return <>
    <PageTitle title="Dataset Explorer">Start with what was measured. All counts and charts use the <strong>{scope}</strong> scope.</PageTitle>
    <section className="panel">
      <h2>Corpus composition</h2>
      <AsyncPanel resource={summary}>{data => <>
        <p><strong>{data.total.toLocaleString()}</strong> retained emails from five canonical SpamAssassin source groups.</p>
        <Balance summary={data} />
        <p className="note">{data.historical_notice}</p>
        <details><summary>Provenance, exclusions and reproducibility</summary>
          <p>Before splitting the source corpus: {data.parse_rejected_count} parse rejections, {data.duplicate_count} duplicate exclusions and {data.label_conflict_count} conflicting-label exclusions. Total excluded: {data.excluded_count}. These counts are global, not assigned to a subset.</p>
          <DataTable caption={`Retained source counts · ${scope}`} columns={['Source group', 'Emails']}
            rows={Object.entries(data.source_groups).map(([group, count]) => [group, count.toLocaleString()])} />
          <DataTable caption="Official archives · acquisition metadata" columns={['Archive', 'Class', 'Acquired (UTC)', 'SHA-256']}
            rows={data.source_archives.map(archive => [<a key={archive.archive_name} href={archive.source_url} target="_blank" rel="noreferrer">{archive.archive_name}</a>, archive.label, archive.acquired_at, <code key={archive.sha256}>{archive.sha256}</code>])} />
          <p className="note">Exact text deduplication precedes the stratified 80/20 split, seed 42. Near duplicates can remain.</p>
          <p className="hash">Dataset ID <code>{data.dataset_id}</code><br />Split ID <code>{data.split_id}</code></p>
        </details>
      </>}</AsyncPanel>
    </section>
    <div className="filter-bar section-gap" aria-label="Dataset chart controls">
      <label>Measurement <select value={metric} onChange={e => setMetric(e.target.value)}>
        <option value="token_count">Token count</option><option value="character_count">Character count</option>
      </select></label>
      <label>Chart class <select value={classLabel} onChange={e => setClassLabel(e.target.value)}>
        {Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <p className="note">Statistics compare both classes. Chart class filters the histogram, box plot and top words.</p>
    </div>
    <section className="panel section-gap">
      <h2>Descriptive statistics</h2>
      <AsyncPanel resource={statistics}>{data => <>
        <DataTable caption={`${data.unit} · ${scope} scope`} columns={['Statistic', 'Ham', 'Spam']}
          rows={metrics.map(([key, label]) => [label, ...['ham', 'spam'].map(group => <NumberValue key={group} value={data.groups[group][key]} />)])} />
        <p className="note">Variance uses squared measurement units and n−1; standard deviation uses {data.unit}. Quartiles use linear interpolation. Tied modes select the smallest value.</p>
        {Object.entries(data.groups).map(([group, stats]) => <div key={group}>
          {stats.mode_tied && <p className="note">{labels[group]}: mode is tied; the smallest tied mode is shown.</p>}<Notes items={stats.notes} />
        </div>)}
      </>}</AsyncPanel>
    </section>
    <AsyncPanel resource={distribution}>{data => <div className="columns section-gap">
      <section className="panel"><h2>Length distribution</h2>
        <p className="note">{labels[classLabel]} · {scope} · {data.selected_records.toLocaleString()} emails · {data.unit}</p>
        {!data.bins.length ? <p>No observations in this selection.</p> : <>
          <figure><div className="chart" role="img" aria-label={`Histogram: ${data.unit} on x axis; emails per bin on y axis`}>
            <ResponsiveContainer width="100%" height="100%"><BarChart data={data.bins} margin={{ bottom: 24, left: 0, right: 10 }}>
              <CartesianGrid vertical={false} stroke="#e1e8f1" /><XAxis dataKey="lower" tickFormatter={compact} label={{ value: data.unit, position: 'insideBottom', offset: -18 }} tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} width={44} tick={{ fontSize: 11 }} /><Tooltip formatter={value => [value, 'Emails']} labelFormatter={(value, payload) => payload?.[0] ? `${payload[0].payload.lower} to ${payload[0].payload.upper} ${data.unit}` : value} />
              <Bar dataKey="count" fill={classLabel === 'spam' ? '#b95328' : '#14786e'} isAnimationActive={false} />
            </BarChart></ResponsiveContainer>
          </div><figcaption>Y axis: email count. Bin starts shown on x axis; full ranges below.</figcaption></figure>
          <details><summary>Histogram values and boundaries</summary><p className="note">Each bin includes its lower boundary and excludes its upper boundary. The final bin includes both boundaries.</p>
            <DataTable caption={`Histogram · ${data.unit}`} columns={['Lower', 'Upper', 'Emails']}
              rows={data.bins.map(bin => [String(bin.lower), String(bin.upper), bin.count])} />
          </details>
        </>}
      </section>
      <section className="panel"><h2>Five-number box plot</h2><p className="note">{labels[classLabel]} · {scope} · {data.unit}</p><BoxPlot values={data.boxplot} unit={data.unit} /></section>
    </div>}</AsyncPanel>
    <section className="panel section-gap"><h2>Words that occur most often</h2>
      <p className="note">Document frequency: each word counts once per email. {labels[classLabel]} · {scope} scope. Select a word to inspect its empirical probability.</p>
      <AsyncPanel resource={words}>{data => data.items.length ?
        <DataTable caption={`Top 15 words · ${data.selected_records.toLocaleString()} emails`} columns={['Word', 'Emails containing word', 'Share of selected emails']}
          rows={data.items.map(item => [<button key={item.word} className="link-button" onClick={() => onWord(item.word)}>{item.word}</button>,
            <span key="count" className="frequency-cell"><span className="frequency-bar" style={{ width: `${item.count / data.selected_records * 100}%` }} />{item.count.toLocaleString()}</span>,
            <NumberValue key="share" value={item.count / data.selected_records} percent />])} /> : <p>No token occurrences in this selection.</p>}
      </AsyncPanel>
    </section>
  </>
}
