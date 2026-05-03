export type Route = {
  id: number
  route_id: string
  route_name: string
  route_type?: string | null
  agency?: string | null
}

export type Stop = {
  id: number
  stop_id: string
  stop_name: string
  latitude?: number | null
  longitude?: number | null
}

export type PredictionResult = {
  delay_probability: number
  expected_delay_minutes: number
  delay_range: string
  confidence: string
  top_factors: string[]
}

export type DelayBucket = {
  hour?: number
  day?: string
  average_delay: number
  count: number
}

export type DelaySummary = {
  average_delay: number
  percent_delayed: number
  most_common_delay_hour: number | null
  worst_day_of_week: string | null
  reliability_score: number
  delay_by_hour: DelayBucket[]
  delay_by_day: DelayBucket[]
  sample_size: number
}

export type Alert = {
  id: number
  route_id?: string | null
  stop_id?: string | null
  alert_header?: string | null
  alert_description?: string | null
  cause?: string | null
  effect?: string | null
  start_time?: string | null
  end_time?: string | null
}

export type PredictionRequest = {
  route_id: string
  stop_id?: string | null
  datetime: string
}
