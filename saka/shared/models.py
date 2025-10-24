from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum

# ==============================================================================
# ENUMS - Fonte única da verdade para valores categóricos
# ==============================================================================

class AgentName(str, Enum):
    """Nomes canônicos para cada agente, usados para roteamento e logging."""
    KAMILA = "kamila_ceo"
    POLARIS = "polaris_advisor"
    ORION = "orion_cfo"
    AETHERTRADER = "aethertrader_manager"
    ATHENA = "athena_sentiment"
    SENTINEL = "sentinel_risk"
    HERMES = "hermes_hf"
    CRONOS = "cronos_cycles"
    GAIA = "gaia_diversification"
    ORCHESTRATOR = "orchestrator"

class TradeSignal(str, Enum):
    """Sinais de negociação padronizados."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class TradeType(str, Enum):
    """Tipos de ordem padronizados."""
    MARKET = "market"
    LIMIT = "limit"

class MacroImpact(str, Enum):
    """Níveis de impacto de eventos macroeconômicos."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# ==============================================================================
# MODELOS DE DADOS - Contratos de API para comunicação entre agentes
# ==============================================================================

# --- Modelos de Requisição (Inputs para os agentes) ---

class AnalysisRequest(BaseModel):
    """Requisição genérica para análise de um ativo."""
    asset: str = Field(..., description="O ativo a ser analisado, ex: 'BTC/USD'")
    historical_prices: Optional[List[float]] = Field(None, description="Lista de preços de fechamento recentes para análises de volatilidade ou técnicas.")

# --- Modelos de Resposta (Outputs dos agentes de análise) ---

class SentinelRiskOutput(BaseModel):
    asset: str
    risk_level: float = Field(..., ge=0.0, le=1.0, description="Nível de risco normalizado de 0 a 1.")
    volatility: float = Field(..., description="Volatilidade calculada (desvio padrão dos retornos).")
    can_trade: bool = Field(..., description="Veto de segurança. Se False, a negociação deve ser bloqueada.")
    reason: str

class AthenaSentimentOutput(BaseModel):
    asset: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    signal: TradeSignal
    confidence: float = Field(..., ge=0.0, le=1.0)

# --- Modelos para o Fluxo de Decisão e Execução ---

class ConsolidatedDataInput(BaseModel):
    """Input para a Kamila, agregando todas as análises."""
    asset: str
    sentinel_analysis: SentinelRiskOutput
    athena_analysis: Optional[AthenaSentimentOutput] = None
    # Adicionar outros outputs de análise aqui (Cronos, Orion, etc.)

class KamilaFinalDecision(BaseModel):
    """Decisão final da Kamila, enviada para execução."""
    action: Literal["execute_trade", "hold"]
    agent_target: Optional[AgentName] = None
    asset: Optional[str] = None
    trade_type: Optional[TradeType] = None
    side: Optional[TradeSignal] = None
    amount_usd: Optional[float] = None
    reason: str

class TradeExecutionReceipt(BaseModel):
    """Recibo de uma ordem executada pelo Aethertrader."""
    trade_id: str
    status: Literal["success", "failed"]
    asset: str
    side: TradeSignal
    executed_price: float
    amount_usd: float
    timestamp: str

# --- Modelo de Erro Padrão ---

class ErrorResponse(BaseModel):
    """Resposta de erro padronizada para todas as APIs."""
    error: str
    details: Optional[str] = None
    source_agent: AgentName