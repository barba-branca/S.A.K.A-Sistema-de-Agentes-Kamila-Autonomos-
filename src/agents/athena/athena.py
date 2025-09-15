import os
import requests
import google.generativeai as genai
from src.core.agent import BaseAgent, Message

class AthenaAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="athena",
            name="Athena",
            description="Analisa o sentimento do mercado a partir de mídias sociais e notícias.",
            orchestrator_url=orchestrator_url
        )
        self.news_api_key = os.getenv("NEWSAPI_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.news_api_key:
            self.logger.warning("Variável de ambiente NEWSAPI_KEY não definida. Athena não pode buscar notícias.")
        if not self.gemini_api_key:
            self.logger.warning("Variável de ambiente GEMINI_API_KEY não definida. Athena não pode analisar sentimentos.")
        else:
            genai.configure(api_key=self.gemini_api_key)
            # Usando um nome de modelo mais específico e estável
            self.genai_model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def fetch_news(self, topic: str, language: str = 'pt', page_size: int = 20):
        """Busca artigos de notícias sobre um determinado tópico na NewsAPI."""
        if not self.news_api_key:
            self.logger.error("Não é possível buscar notícias, a NEWSAPI_KEY não está configurada.")
            return None

        url = (f"https://newsapi.org/v2/everything?"
               f"q={topic}&"
               f"language={language}&"
               f"pageSize={page_size}&"
               f"apiKey={self.news_api_key}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            self.logger.info(f"Buscou {len(articles)} artigos para o tópico '{topic}'.")

            # Filtra artigos sem título e retorna apenas títulos válidos
            valid_titles = []
            for article in articles:
                title = article.get('title')
                if title:
                    valid_titles.append(title)

            self.logger.info(f"Encontrou {len(valid_titles)} títulos válidos.")
            return valid_titles
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao buscar notícias da NewsAPI: {e}")
            return None

    def analyze_sentiment(self, titles: list[str]):
        """Analisa o sentimento de uma lista de textos usando a API do Gemini."""
        if not self.gemini_api_key or not hasattr(self, 'genai_model'):
            self.logger.error("Não é possível analisar o sentimento, a API do Gemini não está configurada.")
            return None

        if not titles:
            self.logger.warning("Nenhum título fornecido para análise.")
            return "Neutro (sem notícias)"

        titles_formatted = "\n- ".join(titles)
        prompt = (
            "Analise o sentimento geral dos seguintes títulos de notícias de uma a cinco palavras (ex: 'Muito Positivo', 'Neutro', 'Negativo'). "
            "Considere o impacto potencial no mercado de criptomoedas, especificamente para o ativo em questão. "
            "Responda apenas com a classificação do sentimento.\n\n"
            "Títulos:\n"
            f"- {titles_formatted}"
        )

        try:
            self.logger.info("Enviando prompt para o Gemini para análise de sentimento...")
            response = self.genai_model.generate_content(prompt)
            sentiment = response.text.strip()
            self.logger.info(f"Sentimento recebido do Gemini: {sentiment}")
            return sentiment
        except Exception as e:
            self.logger.error(f"Erro ao analisar sentimento com a API do Gemini: {e}")
            return None

    async def handle_message(self, message: Message):
        """Lida com comandos para analisar o sentimento de um tópico."""
        self.logger.info(f"Recebeu uma mensagem de {message.sender_id}: {message.content}")

        content = message.content
        command = content.get("command")
        topic = content.get("topic")

        if command == "analyze_sentiment" and topic:
            self.logger.info(f"Iniciando análise de sentimento para o tópico: {topic}")
            titles = self.fetch_news(topic)
            if titles is not None:
                sentiment = self.analyze_sentiment(titles)
                if sentiment:
                    return {"status": "Análise completa", "topic": topic, "sentiment": sentiment}
                else:
                    return {"status": "erro", "detail": "Falha ao analisar o sentimento."}
            else:
                return {"status": "erro", "detail": "Falha ao buscar notícias."}

        return {"status": "erro", "detail": f"Comando inválido ou tópico ausente. Recebido: {content}"}
