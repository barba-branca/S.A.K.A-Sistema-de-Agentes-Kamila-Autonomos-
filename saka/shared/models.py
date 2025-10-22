from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum

# --- Enums para Padronização ---

class AgentName(str, Enum):
    KAMILA = "kamila_ceo"
    POLARIS = "polaris_advisor"
    ORION = "orion_cfo"
    AETHERTRADER = "aethertrader_manager"
    ATHENA = "athena_sentiment"
    SENTINEL = "sentinel_risk"
    HERMES = "hermes_hf"
    CRONOS = "cronos_cycles"
    GAIA = "gaia_diversification"

class TradeSignal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class TradeType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

# --- Modelos de Input/Output para Agentes de Análise ---

class AthenaSentimentOutput(BaseModel):
    asset: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    signal: TradeSignal
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_summary: str

class SentinelRiskOutput(BaseModel):
    asset: str
    risk_level: float = Field(..., ge=0.0, le=1.0)
    volatility: float
    can_trade: bool = True
    reason: Optional[str] = None

class CronosTechnicalOutput(BaseModel):
    """Output de Cronos: Análise técnica."""
    asset: str
    rsi: float = Field(..., description="Índice de Força Relativa (RSI) de 14 dias")
    summary: str

# --- Modelos para Decisão e Execução ---

class TradeDecisionProposal(BaseModel):
    asset: str
    trade_type: TradeType
    side: TradeSignal
    amount_usd: float
    reasoning: str

class PolarisRecommendation(BaseModel):
    decision_approved: bool
    confidence: float
    remarks: Optional[str] = None

class KamilaFinalDecision(BaseModel):
    action: Literal["execute_trade"]
    agent_target: Literal[AgentName.AETHERTRADER, AgentName.HERMES]
    asset: str
    trade_type: TradeType
    side: Literal["buy", "sell"]
    amount_usd: float

class TradeExecutionReceipt(BaseModel):
    trade_id: str
    status: Literal["success", "failed"]
    executed_price: float
    timestamp: str

# --- Modelo para Agregação de Dados para Kamila ---

class ConsolidatedDataInput(BaseModel):
    asset: str
    athena_analysis: AthenaSentimentOutput
    sentinel_analysis: SentinelRiskOutput
    cronos_analysis: CronosTechnicalOutput