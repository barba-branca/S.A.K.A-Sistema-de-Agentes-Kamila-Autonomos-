from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum

class AgentName(str, Enum):
    KAMILA = "kamila_ceo"; POLARIS = "polaris_advisor"; ORION = "orion_cfo"; AETHERTRADER = "aethertrader_manager"; ATHENA = "athena_sentiment"; SENTINEL = "sentinel_risk"; HERMES = "hermes_hf"; CRONOS = "cronos_cycles"; GAIA = "gaia_diversification"
class TradeSignal(str, Enum):
    BUY = "buy"; SELL = "sell"; HOLD = "hold"
class TradeType(str, Enum):
    MARKET = "market"; LIMIT = "limit"
class MacroImpact(str, Enum):
    HIGH = "high"; MEDIUM = "medium"; LOW = "low"

class AnalysisRequest(BaseModel):
    asset: str
    historical_prices: Optional[List[float]] = None

class SentinelRiskOutput(BaseModel):
    asset: str; risk_level: float; volatility: float; can_trade: bool; reason: str
class CronosTechnicalOutput(BaseModel):
    asset: str; rsi: float; macd_line: float; signal_line: float; histogram: float; is_bullish_crossover: bool; is_bearish_crossover: bool
class OrionMacroOutput(BaseModel):
    asset: str; impact: MacroImpact; event_name: str; summary: str
class AthenaSentimentOutput(BaseModel):
    asset: str; sentiment_score: float; signal: TradeSignal; confidence: float

class TradeProposal(BaseModel):
    asset: str; side: TradeSignal; trade_type: TradeType; entry_price: float; reasoning: str
class PolarisApproval(BaseModel):
    decision_approved: bool; remarks: str

class GaiaPositionSizingRequest(BaseModel):
    asset: str; entry_price: float
class GaiaPositionSizingResponse(BaseModel):
    asset: str; amount_usd: float; reasoning: str

class ConsolidatedDataInput(BaseModel):
    asset: str; current_price: float; sentinel_analysis: SentinelRiskOutput; cronos_analysis: CronosTechnicalOutput; orion_analysis: OrionMacroOutput; athena_analysis: AthenaSentimentOutput
class KamilaFinalDecision(BaseModel):
    action: str; agent_target: Optional[AgentName] = None; asset: Optional[str] = None; trade_type: Optional[TradeType] = None; side: Optional[TradeSignal] = None; amount_usd: Optional[float] = None; reason: str
class TradeExecutionReceipt(BaseModel):
    order_id: str; trade_id: Optional[str] = None; status: str; asset: str; side: TradeSignal; executed_price: float; executed_quantity: float; amount_usd: float; timestamp: str; raw_response: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str; details: Optional[str] = None; source_agent: AgentName