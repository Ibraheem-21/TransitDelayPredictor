# API Contract

## GET /health

Returns backend status.

## GET /routes

Returns all GO routes.

## GET /stops

Query params:

- `route_id` optional

Returns all stops or stops served by the selected route.

## GET /delays/history

Query params:

- `route_id`
- `stop_id` optional
- `start_date` optional ISO datetime
- `end_date` optional ISO datetime

Returns realtime delay observations.

## GET /delays/summary

Query params:

- `route_id`
- `stop_id` optional

Returns average delay, percent delayed, worst hour, worst day, reliability score, chart buckets, and sample size.

## POST /predict

Request:

```json
{
  "route_id": "string",
  "stop_id": "string",
  "datetime": "2026-05-03T08:30:00"
}
```

Response:

```json
{
  "delay_probability": 0.64,
  "expected_delay_minutes": 8,
  "delay_range": "5-12 minutes",
  "confidence": "medium",
  "top_factors": ["rush hour", "recent route delays", "rain"]
}
```

## GET /alerts

Query params:

- `route_id` optional

Returns active service alerts.
