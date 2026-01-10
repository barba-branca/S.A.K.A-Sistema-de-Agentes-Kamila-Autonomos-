import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from saka.orchestrator.main import get_kamila_decision, app, lifespan
from saka.shared.models import AnalysisRequest, SentinelRiskOutput, CronosTechnicalOutput, OrionMacroOutput, AgentName, MacroImpact

# Mock dependencies
@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def analysis_request():
    return AnalysisRequest(asset="BTC/USD", historical_prices=[100, 101, 102])

@pytest.mark.asyncio
async def test_get_kamila_decision_client_usage(mock_httpx_client, analysis_request):
    """
    Verify that the current implementation works and uses a client.
    """

    # Mock responses for parallel calls
    def make_response(json_data):
        # We need to construct the response such that raise_for_status doesn't fail
        # OR we can mock raise_for_status.
        # Since the error is "Cannot call `raise_for_status` as the request instance has not been set",
        # let's set the request!
        req = httpx.Request("POST", "http://test")
        r = httpx.Response(200, json=json_data, request=req)
        return r

    response_sentinel = make_response({"asset": "BTC/USD", "risk_level": 0.1, "volatility": 0.02, "can_trade": True, "reason": "Low risk", "source_agent": AgentName.SENTINEL})
    response_cronos = make_response({"asset": "BTC/USD", "rsi": 40.0, "source_agent": AgentName.CRONOS})
    response_orion = make_response({"asset": "BTC/USD", "impact": MacroImpact.LOW, "event_name": "None", "summary": "No events", "source_agent": AgentName.ORION})

    # Mock Kamila response
    response_kamila = make_response({"action": "hold", "reason": "Test decision"})

    # We create a side_effect function that returns the correct response based on the input
    async def post_side_effect(url, *args, **kwargs):
        if "kamila" in str(url).lower():
            return response_kamila
        # Return a response with a request set, to avoid RuntimeError
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, request=req)

    # Note: In the latest failure, it failed at kamila_response.json().
    # This means the post_side_effect returned a response, but we need to ensure
    # the one returned for "kamila" is actually response_kamila which has json content.
    # The side_effect logic seems correct for that: if "kamila" in url.
    # Wait, the URL is f"{KAMILA_URL}/decide". If KAMILA_URL is None or something, maybe it fails?
    # But let's check the test failure again. It says JSONDecodeError.
    # This implies response.text is empty.
    # Ah, httpx.Response(200, request=req) creates an empty body response.
    # And my side effect returns that for non-kamila calls.
    # But wait, the Kamila call IS the one we care about for the final return.

    mock_httpx_client.post.side_effect = post_side_effect

    # We also need to mock asyncio.gather because get_kamila_decision uses it
    with patch("asyncio.gather", new_callable=AsyncMock) as mock_gather:
        mock_gather.return_value = [response_sentinel, response_cronos, response_orion]

        # Ensure environment variable is mocked if used in URL construction,
        # but the function uses global constants loaded at import time.
        # We can assume KAMILA_URL is None or whatever it was when imported.
        # So "None/decide" might be the URL. "None" is in the string.
        # Let's adjust the check.

        async def post_side_effect_robust(url, *args, **kwargs):
            url_str = str(url).lower()
            if "decide" in url_str: # KAMILA_URL likely ends with /decide in the call
                return response_kamila
            req = httpx.Request("POST", str(url))
            return httpx.Response(200, request=req)

        mock_httpx_client.post.side_effect = post_side_effect_robust

        result = await get_kamila_decision(analysis_request)

        assert result["action"] == "hold"

@pytest.mark.asyncio
async def test_lifespan_creates_global_client():
    """Verify that lifespan creates and destroys the global client."""
    from saka.orchestrator import main

    # Ensure it's None initially
    main.http_client = None

    async with main.lifespan(app):
        assert main.http_client is not None
        assert isinstance(main.http_client, httpx.AsyncClient)

        # Mock aclose to verify it's called
        main.http_client.aclose = AsyncMock()

    main.http_client.aclose.assert_called_once()
