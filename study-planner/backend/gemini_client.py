import os
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# ==============================
# Cargar variables de entorno
# ==============================
load_dotenv()  # Carga .env automáticamente

# Verificar que la API key se cargó correctamente
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY no encontrada. Asegúrate de que esté en tu archivo .env"
    )
else:
    print(f"API Key cargada correctamente: {API_KEY[:5]}...")  # Solo los primeros 5 caracteres

# ==============================
# Función de búsqueda web
# ==============================
def perform_web_search(query: str, max_results: int = 6) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    try:
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                if not isinstance(result, dict):
                    continue
                title = result.get("title") or ""
                href = result.get("href") or ""
                body = result.get("body") or ""
                if title and href:
                    results.append({"title": title, "href": href, "body": body})
        return results
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []

# ==============================
# Clase GeminiClient
# ==============================
class GeminiClient:
    def __init__(self):
        try:
            genai.configure(api_key=API_KEY)

            self.model = genai.GenerativeModel("models/gemini-2.5-flash-lite")

            # Historial de conversación
            self.chat = self.model.start_chat(history=[])

            # Estado del agente de viajes
            self.state = {
                "destination": None,
                "budget": None,
                "dates": None,
                "travelers": None,
                "interests": None,
            }

            print("✈️ Travel Agent AI inicializado correctamente.")

        except Exception as e:
            print(f"Error configuring Gemini API: {e}")
            self.chat = None

    # -----------------------------
    # Detectar info clave del usuario
    # -----------------------------
    def _update_state_from_input(self, text: str):
        """
        Usa Gemini para extraer información estructurada del mensaje del usuario
        y actualizar el estado del agente.
        """
        extraction_prompt = f"""
        Extract travel-related information from the message below.
        Return ONLY valid JSON with these keys (null if missing):
        - destination
        - budget
        - dates
        - travelers
        - interests

        Message:
        "{text}"
        """

        try:
            result = self.model.generate_content(extraction_prompt)
            data = eval(result.text) if result.text else {}
            if isinstance(data, dict):
                for k in self.state:
                    if data.get(k):
                        self.state[k] = data[k]
        except Exception:
            pass  # extracción best-effort

    # -----------------------------
    # Ver qué falta preguntar
    # -----------------------------
    def _missing_fields(self):
        return [k for k, v in self.state.items() if not v]

    # -----------------------------
    # Respuesta principal
    # -----------------------------
    def generate_response(self, user_input: str) -> str:
        if not self.chat:
            return "Travel service is not configured correctly."

        # Actualizar estado con el input del usuario
        self._update_state_from_input(user_input)

        missing = self._missing_fields()

        # 1️⃣ Si falta información → preguntar
        if missing:
            next_question_prompt = f"""
            You are a friendly AI travel agent.
            Ask ONE clear and concise question to collect the next missing detail.
            Missing details: {", ".join(missing)}.
            Do not ask multiple questions at once.
            """
            response = self.chat.send_message(next_question_prompt)
            return response.text

        # 2️⃣ Si ya tenemos todo → planificar viaje
        planning_prompt = f"""
        You are an expert travel agency.

        Trip details:
        Destination: {self.state['destination']}
        Budget: {self.state['budget']}
        Dates: {self.state['dates']}
        Travelers: {self.state['travelers']}
        Interests: {self.state['interests']}

        Tasks:
        - Analyze the destination
        - Propose a realistic itinerary
        - Suggest accommodations and activities within budget
        - Give travel tips and best areas to stay
        - Present the plan in a clear structure
        """

        response = self.chat.send_message(planning_prompt)
        return response.text
