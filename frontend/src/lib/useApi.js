import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from './api.js'

export function useApi(path) {
  const [revision, setRevision] = useState(0)
  const [result, setResult] = useState(null)
  const key = JSON.stringify([path, revision])
  const retry = useCallback(() => setRevision(value => value + 1), [])
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    apiFetch(path, { signal: controller.signal }).then(
      data => { if (!controller.signal.aborted) setResult({ key, data }) },
      error => { if (!controller.signal.aborted) setResult({ key, error: error.message }) },
    )
    return () => controller.abort()
  }, [path, key])
  return { ...(result?.key === key ? result : {}), loading: Boolean(path && result?.key !== key), retry }
}
