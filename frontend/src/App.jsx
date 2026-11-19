import { lazy, Suspense, useEffect, useState, useSyncExternalStore } from 'react'
import { PageTitle } from './components/common.jsx'
import Dashboard from './pages/Dashboard.jsx'
import { useApi } from './lib/useApi.js'
import './styles.css'

const Dataset = lazy(() => import('./pages/Dataset.jsx'))
const Probability = lazy(() => import('./pages/Probability.jsx'))
const Statistics = lazy(() => import('./pages/Statistics.jsx'))
const Detect = lazy(() => import('./pages/Detect.jsx'))

const routes = [
  ['/', 'Overview', 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z'],
  ['/dataset', 'Dataset Explorer', 'M4 5h16v14H4z M4 10h16 M10 5v14'],
  ['/probability', 'Probability', 'M4 19V9 M10 19V4 M16 19v-7 M22 19H2'],
  ['/statistics', 'Statistical Inference', 'M3 18c4 0 4-12 9-12s5 12 9 12 M3 21h18'],
  ['/detect', 'Spam Detector', 'M3 5h18v14H3z M3 5l9 8 9-8'],
  ['/evaluation', 'Model Evaluation', 'M4 4h16v16H4z M4 12h16 M12 4v16'],
]
function subscribe(callback) {
  window.addEventListener('popstate', callback)
  return () => window.removeEventListener('popstate', callback)
}
function navigate(path) {
  window.history.pushState(null, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

export default function App() {
  const path = useSyncExternalStore(subscribe, () => window.location.pathname)
  const [scope, setScope] = useState('all')
  const [selectedWord, setSelectedWord] = useState('free')
  const health = useApi('/health')
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [path])
  const route = routes.find(item => item[0] === path)
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to analysis</a>
    <aside className="rail">
      <a className="brand" href="/" onClick={event => { event.preventDefault(); navigate('/') }}>
        <svg viewBox="0 0 32 32" aria-hidden="true"><path d="M3 26V14h6v12z M13 26V4h6v22z M23 26V9h6v17z" /></svg>
        <span>MailSense</span>
      </a>
      <p className="rail-caption">Probability in practice</p>
      <nav aria-label="Main navigation">{routes.map(([url, label, icon]) =>
        <a key={url} href={url} aria-current={path === url ? 'page' : undefined}
          onClick={event => { if (!event.ctrlKey && !event.metaKey && !event.shiftKey && event.button === 0) { event.preventDefault(); navigate(url) } }}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d={icon} /></svg>{label}
        </a>)}</nav>
      <div className="rail-footer"><strong>Built for understanding</strong><p>Local analysis. Historical corpus.<br />No inbox connection.</p></div>
    </aside>
    <div className="workspace">
      <header className="workspace-bar">
        <span className="workspace-label">Statistical email analysis</span>
        <div className="toolbar">
          <span className={`service-status ${health.error ? 'unready' : health.data?.status === 'ready' ? 'ready' : ''}`} role="status">
            {health.loading ? 'Checking API…' : health.error ? 'API unavailable' : health.data?.status === 'ready' ? 'Local API ready' : 'Preparation needed'}
          </span>
          <label>Dataset scope <select value={scope} onChange={e => setScope(e.target.value)} disabled={path === '/detect' || path === '/evaluation'}>
            <option value="all">All retained emails</option><option value="train">Training subset</option><option value="test">Test subset</option>
          </select></label>
        </div>
      </header>
      <main id="main-content">
        <Suspense fallback={<div className="state" role="status">Opening analysis…</div>}>
        {path === '/' ? <Dashboard scope={scope} health={health} navigate={navigate} /> :
          path === '/dataset' ? <Dataset scope={scope} onWord={word => { setSelectedWord(word); navigate('/probability') }} /> :
          path === '/probability' ? <Probability scope={scope} word={selectedWord} setWord={setSelectedWord} onInference={() => navigate('/statistics')} /> :
          path === '/statistics' ? <Statistics scope={scope} word={selectedWord} setWord={setSelectedWord} /> :
          path === '/detect' ? <Detect onEvaluation={() => navigate('/evaluation')} /> :
          route ? <><PageTitle title={route[1]}>Inspect the counts, assumptions and evidence behind the result.</PageTitle>
            <section className="panel"><h2>Analysis workspace</h2><p>This module is being connected to the verified local API.</p>{path === '/probability' && <p>Selected word: <strong>{selectedWord}</strong></p>}</section></> :
            <><PageTitle title="Page not found">Choose an analysis from the navigation to continue.</PageTitle><button onClick={() => navigate('/')}>Return to overview</button></>}
        </Suspense>
      </main>
      <footer className="workspace-footer">Educational demonstration · Model estimates are not calibrated certainty.</footer>
    </div>
  </div>
}
