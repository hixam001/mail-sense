import { useEffect, useRef } from 'react'
import { formatNumber } from '../lib/format.js'

export function PageTitle({ title, children }) {
  const heading = useRef(null)
  useEffect(() => { heading.current?.focus({ preventScroll: true }); document.title = `${title} · MailSense` }, [title])
  return <header className="page-title"><h1 ref={heading} tabIndex="-1">{title}</h1><p>{children}</p></header>
}
export function AsyncPanel({ resource, children }) {
  if (resource.loading) return <div className="state" role="status">Loading local analysis…</div>
  if (resource.error) return <div className="state error" role="alert">
    <h2>Analysis unavailable</h2><p>{resource.error}</p>
    <p>Check the local API and prepared corpus/model artifacts, then retry.</p>
    <button onClick={resource.retry}>Retry analysis</button>
  </div>
  if (!resource.data) return <div className="state">No analysis to show yet.</div>
  return children(resource.data)
}
export function Notes({ items = [] }) {
  return items.length ? <ul className="notes">{items.map(item => <li key={item}>{item}</li>)}</ul> : null
}
export function NumberValue({ value, percent = false }) {
  return value == null ? <span title="Undefined for this selection">Undefined</span> :
    <>{formatNumber(value, percent)}</>
}
export function Balance({ summary }) {
  return <div className="balance-block">
    <div className="balance" aria-hidden="true">
      <span className="ham" style={{ width: `${summary.class_proportions.ham * 100}%` }} />
      <span className="spam" style={{ width: `${summary.class_proportions.spam * 100}%` }} />
    </div>
    <div className="balance-labels">
      <span><i className="swatch ham" />Ham (legitimate) <strong>{summary.class_counts.ham.toLocaleString()}</strong></span>
      <span><i className="swatch spam" />Spam <strong>{summary.class_counts.spam.toLocaleString()}</strong></span>
    </div>
  </div>
}
