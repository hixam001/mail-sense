import { useId } from 'react'
import { canonicalWord } from '../lib/validation.js'

export default function WordForm({ value, onChange, onSubmit, buttonLabel = 'Analyze word', children }) {
  const id = useId()
  const valid = canonicalWord(value)
  return <form className="word-form" onSubmit={event => { event.preventDefault(); if (valid) onSubmit(valid) }}>
    <label htmlFor={id}>Word to analyze</label>
    <div className="form-row"><input id={id} value={value} onChange={e => onChange(e.target.value)}
      autoComplete="off" spellCheck="false" aria-invalid={!valid} aria-describedby={`${id}-help`} />
      {children}<button type="submit" disabled={!valid}>{buttonLabel}</button></div>
    <p id={`${id}-help`} className={valid ? 'note' : 'validation'}>{valid ? 'One token, at least two letters, numbers or underscores. Case is normalized.' : 'Enter one token of 2–64 characters, without spaces or punctuation.'}</p>
  </form>
}
