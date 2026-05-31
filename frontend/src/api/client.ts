import axios from 'axios'
import type {
  Alert,
  DataStatus,
  DelaySummary,
  PredictionRequest,
  PredictionResult,
  Reliability,
  Route,
  Stop,
} from '../types/transit'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

export const api = {
  async getRoutes(): Promise<Route[]> {
    const { data } = await http.get('/routes')
    return data
  },
  async getStops(routeId?: string): Promise<Stop[]> {
    const { data } = await http.get('/stops', { params: routeId ? { route_id: routeId } : undefined })
    return data
  },
  async getDelaySummary(routeId: string, stopId?: string): Promise<DelaySummary> {
    const { data } = await http.get('/delays/summary', { params: { route_id: routeId, stop_id: stopId } })
    return data
  },
  async getDataStatus(): Promise<DataStatus> {
    const { data } = await http.get('/delays/data-status')
    return data
  },
  async getAlerts(routeId?: string): Promise<Alert[]> {
    const { data } = await http.get('/alerts', { params: routeId ? { route_id: routeId } : undefined })
    return data
  },
  async predict(payload: PredictionRequest): Promise<PredictionResult> {
    const { data } = await http.post('/predict', payload)
    return data
  },
  async getReliability(routeId: string, stopId?: string): Promise<Reliability> {
    const { data } = await http.get('/reliability', { params: { route_id: routeId, stop_id: stopId } })
    return data
  },
}
