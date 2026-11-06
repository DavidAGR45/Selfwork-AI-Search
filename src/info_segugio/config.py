import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Cloud
class OpenAIConfig:
    AI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")
    AI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# LLM in Locale
class OllamaConfig:
    AI_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1")
    AI_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")
    MODEL = os.getenv("OLLAMA_MODEL", "lfm3:latest")

# Ricerca Web Tavily
class TavilyConfig:
    API_KEY = os.getenv("TAVILY_API_KEY", "")

# Scegli la configurazione attiva (OpenAIConfig oppure OllamaConfig)
# Può essere controllata da .env (AI_PROVIDER=openai o AI_PROVIDER=ollama) o impostata direttamente
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()
if AI_PROVIDER == "openai":
    Config = OpenAIConfig
else:
    Config = OllamaConfig

# Riferimenti per accedere direttamente:
Config.OpenAI = OpenAIConfig
Config.Ollama = OllamaConfig
Config.Tavily = TavilyConfig
Config.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Alias retrocompatibilità
Confing = Config
