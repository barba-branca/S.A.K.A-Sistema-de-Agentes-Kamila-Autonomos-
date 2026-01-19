## 2026-01-19 - Synchronous API calls in loops
**Learning:** The backtesting script (`scripts/backtest.py`) was creating a new TCP connection for every simulation step (thousands of requests), causing significant overhead (1.4x slowdown on localhost, potentially much worse on network).
**Action:** Always use `requests.Session()` (or `httpx.Client`/`AsyncClient`) with a context manager when making repeated API calls in a loop to leverage connection pooling.
