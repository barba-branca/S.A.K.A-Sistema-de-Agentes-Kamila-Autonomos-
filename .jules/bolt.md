## 2024-05-22 - [Truncation of Time-Series Data]
**Learning:** Agents often receive full historical datasets (e.g., from the beginning of time) via the Orchestrator, but many metrics (volatility, RSI, etc.) only require a recent window. Naively processing the full list leads to O(N) performance where N grows indefinitely.
**Action:** Always check if an agent's metric calculation can be truncated to a fixed window (e.g., 500 periods) to ensure O(1) performance relative to total history. Implement this truncation early in the processing pipeline (before numpy/pandas conversion).
