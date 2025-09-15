import os
import google.generativeai as genai
from alpha_vantage.timeseries import TimeSeries
from src.core.agent import BaseAgent, Message
import json

class OrionAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="orion",
            name="Orion",
            description="Analisa tendências macroeconômicas, relatórios financeiros e fornece inputs estratégicos.",
            orchestrator_url=orchestrator_url
        )
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.alpha_vantage_key:
            self.logger.warning("ALPHA_VANTAGE_KEY não definida. Orion não pode buscar dados financeiros.")
        if not self.gemini_api_key:
            self.logger.warning("GEMINI_API_KEY não definida. Orion não pode analisar dados.")
        else:
            genai.configure(api_key=self.gemini_api_key)
            self.genai_model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def fetch_market_data(self, symbol: str):
        """Busca dados de séries temporais para um símbolo da Alpha Vantage."""
        if not self.alpha_vantage_key:
            self.logger.error("Não é possível buscar dados, ALPHA_VANTAGE_KEY não configurada.")
            return None
        try:
            self.logger.info(f"Buscando dados de mercado para o símbolo: {symbol}")
            ts = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='compact')
            # Pega os dados dos últimos 5 dias para análise
            latest_data = data.head(5)
            self.logger.info(f"Dados de mercado para {symbol} buscados com sucesso.")
            return latest_data.to_json(orient='split')
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados da Alpha Vantage para {symbol}: {e}")
            return None

    def analyze_market_data(self, data_json: str):
        """Analisa dados de mercado usando a API do Gemini."""
        if not self.gemini_api_key or not hasattr(self, 'genai_model'):
            self.logger.error("Não é possível analisar dados, API do Gemini não configurada.")
            return None

        prompt = (
            "Você é um analista financeiro sênior. Analise os seguintes dados de mercado de ações (formato JSON) dos últimos 5 dias. "
            "Forneça um breve resumo (2-3 frases) sobre a tendência recente (alta, baixa, estável) e o que isso pode indicar. "
            "Seja conciso e direto.\n\n"
            f"Dados:\n{data_json}"
        )

        try:
            self.logger.info("Enviando dados de mercado para análise do Gemini...")
            response = self.genai_model.generate_content(prompt)
            analysis = response.text.strip()
            self.logger.info(f"Análise recebida do Gemini: {analysis}")
            return analysis
        except Exception as e:
            self.logger.error(f"Erro ao analisar dados com a API do Gemini: {e}")
            return None

    async def handle_message(self, message: Message):
        """Lida com comandos para buscar e analisar dados macroeconômicos."""
        self.logger.info(f"Recebeu uma mensagem de {message.sender_id}: {message.content}")

        content = message.content
        command = content.get("command")
        symbol = content.get("symbol")

        if command == "analyze_market" and symbol:
            self.logger.info(f"Iniciando análise de mercado para o símbolo: {symbol}")
            market_data = self.fetch_market_data(symbol)
            if market_data:
                analysis = self.analyze_market_data(market_data)
                if analysis:
                    return {"status": "Análise completa", "symbol": symbol, "analysis": analysis}
                else:
                    return {"status": "erro", "detail": "Falha ao analisar os dados de mercado."}
            else:
                return {"status": "erro", "detail": "Falha ao buscar os dados de mercado."}

        return {"status": "erro", "detail": f"Comando inválido ou símbolo ausente. Recebido: {content}"}
