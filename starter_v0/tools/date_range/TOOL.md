---
name: date_range
track: bonus
kind: local_formatter
provider: python_datetime
requires_env: []
inputs: [phrase, today]
outputs: [phrase, start_date, end_date, timeframe]
side_effect: false
---
# date_range

Converts a relative time phrase in Vietnamese or English ("hôm nay", "tuần này",
"tháng này", "năm nay", "today", "this week"...) into concrete ISO dates plus the
`timeframe` enum (`day|week|month|year`) used by `lookup`. Local only, no network.