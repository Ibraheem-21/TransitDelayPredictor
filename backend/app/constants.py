"""Shared constants for GOPredict.

The app focuses exclusively on GO Transit rail (train) service. GTFS uses
``route_type`` 2 for rail, which is how rail routes are distinguished from the
agency's bus routes throughout the codebase.
"""

# GTFS route_type for rail/train service.
RAIL_ROUTE_TYPE = "2"

# Source label for observations pulled from the live GTFS Realtime feed.
LIVE_SOURCE = "gtfs-realtime"

# A single train delay above this is treated as a data error and discarded
# (12 hours in seconds). Protects aggregates from corrupt feed values.
MAX_PLAUSIBLE_DELAY_SECONDS = 12 * 60 * 60

# A trip counts as "delayed" once it is at least this many minutes behind.
DELAY_THRESHOLD_MINUTES = 5.0
