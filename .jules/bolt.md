# Bolt's Journal

## 2025-01-11 - [RSI Calculation & Historical Data]
**Learning:** For technical indicators using Exponential Moving Average (EMA) like RSI, `pandas.ewm` calculation time scales linearly O(N) with the size of the input series. However, due to the exponential decay of weights, data points beyond a certain historical window (e.g., 35x the period) have negligible impact (< machine epsilon).
**Action:** When optimizing technical indicators, always truncate historical data to `max(safe_minimum, period * safety_factor)` before calculation. This transforms O(N) complexity into O(1) relative to total history, preventing performance cliffs as data accumulates.
