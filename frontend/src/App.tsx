import { useEffect, useState } from 'react'
import { AlertTriangle, BarChart3, Clock, RefreshCw, Search } from 'lucide-react'
import { AlertsPanel } from './components/AlertsPanel'
import { DateTimePicker } from './components/DateTimePicker'
import { DelayChart } from './components/DelayChart'
import { ErrorMessage } from './components/ErrorMessage'
import { LoadingSpinner } from './components/LoadingSpinner'
import { Navbar } from './components/Navbar'
import { PredictionCard } from './components/PredictionCard'
import { ReliabilityScoreCard } from './components/ReliabilityScoreCard'
import { RouteSelector } from './components/RouteSelector'
import { StopSelector } from './components/StopSelector'
import { api } from './api/client'
import type { Alert, DelaySummary, PredictionResult, Reliability, Route, Stop } from './types/transit'

function localDateTimeValue() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
}

function App() {
  const [routes, setRoutes] = useState<Route[]>([])
  const [stops, setStops] = useState<Stop[]>([])
  const [selectedRoute, setSelectedRoute] = useState('')
  const [selectedStop, setSelectedStop] = useState('')
  const [dateTime, setDateTime] = useState(localDateTimeValue)
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [summary, setSummary] = useState<DelaySummary | null>(null)
  const [reliability, setReliability] = useState<Reliability | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getRoutes().then(setRoutes).catch(() => setError('Backend is not reachable or no rail routes are loaded yet.'))
  }, [])

  const selectRoute = (routeId: string) => {
    setSelectedRoute(routeId)
    setStops([])
    setSelectedStop('')
    setPrediction(null)
    setSummary(null)
    setReliability(null)
    setAlerts([])
    setError('')
    if (!routeId) return

    setLoading(true)
    Promise.all([
      api.getStops(routeId),
      api.getDelaySummary(routeId),
      api.getAlerts(routeId),
      api.getReliability(routeId),
    ])
      .then(([nextStops, nextSummary, nextAlerts, nextReliability]) => {
        setStops(nextStops)
        setSummary(nextSummary)
        setAlerts(nextAlerts)
        setReliability(nextReliability)
      })
      .catch(() => setError('Could not load route details. Check the backend logs.'))
      .finally(() => setLoading(false))
  }

  const runPrediction = async () => {
    if (!selectedRoute) {
      setError('Choose a rail line first.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const result = await api.predict({
        route_id: selectedRoute,
        stop_id: selectedStop || null,
        datetime: new Date(dateTime).toISOString(),
      })
      setPrediction(result)
      const [nextSummary, nextReliability] = await Promise.all([
        api.getDelaySummary(selectedRoute, selectedStop || undefined),
        api.getReliability(selectedRoute, selectedStop || undefined),
      ])
      setSummary(nextSummary)
      setReliability(nextReliability)
    } catch {
      setError('Prediction failed. Check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f5f7fb] text-slate-900">
      <Navbar />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <section className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-50 text-emerald-700">
                <Search className="h-5 w-5" />
              </div>
              <h1 className="text-xl font-semibold tracking-normal">GO Rail Delay Predictor</h1>
            </div>
            <div className="grid max-w-4xl gap-4 lg:grid-cols-2">
              <div className="rounded-md border border-slate-200 bg-slate-50/70 p-3">
                <RouteSelector routes={routes} value={selectedRoute} onChange={selectRoute} />
              </div>
              <div className="grid gap-3 rounded-md border border-slate-200 bg-slate-50/70 p-3">
                <StopSelector stops={stops} value={selectedStop} onChange={setSelectedStop} disabled={!selectedRoute} />
                <DateTimePicker value={dateTime} onChange={setDateTime} />
              </div>
            </div>
            <div className="mt-4 flex">
              <button
                type="button"
                onClick={runPrediction}
                className="inline-flex min-h-11 w-full max-w-xs items-center justify-center gap-2 rounded-md bg-emerald-700 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={loading}
              >
                {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Clock className="h-4 w-4" />}
                Predict
              </button>
            </div>
            {error && <ErrorMessage message={error} />}
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <h2 className="text-base font-semibold">Active Alerts</h2>
            </div>
            <AlertsPanel alerts={alerts} />
          </div>
        </section>

        {loading && <LoadingSpinner />}

        <section className="grid gap-4 lg:grid-cols-2">
          <PredictionCard prediction={prediction} />
          <ReliabilityScoreCard reliability={reliability} />
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm lg:col-span-1">
            <div className="mb-3 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-sky-700" />
              <h2 className="text-base font-semibold">Selected route stats</h2>
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <Metric label="Average delay" value={`${summary?.average_delay ?? 0} min`} />
              <Metric label="Delayed trips" value={`${summary?.percent_delayed ?? 0}%`} />
              <Metric label="Worst hour" value={summary?.most_common_delay_hour == null ? 'N/A' : `${summary.most_common_delay_hour}:00`} />
              <Metric label="Worst day" value={summary?.worst_day_of_week ?? 'N/A'} />
            </dl>
          </div>
          <div className="lg:col-span-2">
            <div className="grid gap-4 lg:grid-cols-2">
              <DelayChart title="Delays by Hour of Day" subtitle="Collected live samples by local hour" data={summary?.delay_by_hour ?? []} xKey="hour" />
              <DelayChart title="Delays by Day of Week" subtitle="Collected live samples by local day" data={summary?.delay_by_day ?? []} xKey="day" />
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <dt className="text-xs uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 text-lg font-semibold">{value}</dd>
    </div>
  )
}

export default App
