import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiFetch } from './api.js'

export function useApi(path, body) {
  const [revision, setRevision] = useState(0)
  const [result, setResult] = useState(null)
  const payload = JSON.stringify(body)
  const key = JSON.stringify([path, payload, revision])
  // Keep request identity without retaining input content in the result's identifier.
  const generation = useMemo(() => Symbol(key ? 'request' : 'idle'), [key])
  const retry = useCallback(() => setRevision(value => value + 1), [])
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    apiFetch(path, { signal: controller.signal, ...(payload ? { body: JSON.parse(payload) } : {}) }).then(
      data => { if (!controller.signal.aborted) setResult({ generation, data }) },
      error => { if (!controller.signal.aborted) setResult({ generation, error: error.message }) },
    )
    return () => controller.abort()
  }, [path, payload, generation])
  return { ...(result?.generation === generation ? result : {}), loading: Boolean(path && result?.generation !== generation), retry }
}
