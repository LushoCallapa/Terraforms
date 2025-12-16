import os
import google.generativeai as genai
from dotenv import load_dotenv

# ===========================
# Cargar API Key
# ===========================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY no encontrada en .env")

# ===========================
# Clase GeminiClient
# ===========================
class GeminiClient:
    def __init__(self):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        self.chat = self.model.start_chat(history=[])
        
        # Estado interno del viaje
        self.state = {
            "destination": None,
            "budget": None,
            "dates": None,
            "travelers": None,
            "interests": None,
            "constraints": None,
        }
        # Historial de la conversación completo
        self.history = []

    def _missing_fields(self):
        """Devuelve lista de campos aún no completados."""
        return [k for k, v in self.state.items() if not v]

    def _update_state_from_input(self, text):
        """Actualiza el estado según la entrada del usuario."""
        text_lower = text.lower()

        # Guardar input en el historial
        self.history.append({"role": "user", "content": text})

        # =========================
        # Detectar restricciones
        # =========================
        if self.state["constraints"] is None:
            if any(word in text_lower for word in ["no", "ninguna", "n/a"]):
                self.state["constraints"] = "ninguna"
            else:
                self.state["constraints"] = text  # cualquier otra respuesta se guarda

        # =========================
        # Presupuesto
        # =========================
        if self.state["budget"] is None and ("bolivianos" in text_lower or "$" in text_lower):
            self.state["budget"] = text

        # =========================
        # Fechas
        # =========================
        if self.state["dates"] is None:
            months = ["enero","febrero","marzo","abril","mayo","junio","julio",
                      "agosto","septiembre","octubre","noviembre","diciembre"]
            if any(month in text_lower for month in months):
                self.state["dates"] = text

        # =========================
        # Destino (Cualquier lugar del mundo)
        # =========================
        if self.state["destination"] is None:
            # Tomamos cualquier respuesta como destino si aún no se ha asignado
            self.state["destination"] = text

        # =========================
        # Intereses
        # =========================
        if self.state["interests"] is None:
            if any(word in text_lower for word in ["cultura", "gastronomía", "naturaleza", "playa", "aventura", "todo"]):
                self.state["interests"] = text
            else:
                # También aceptamos cualquier respuesta como intereses
                self.state["interests"] = text

        # =========================
        # Viajeros
        # =========================
        if self.state["travelers"] is None:
            if any(word in text_lower for word in ["persona","adulto","niño","2","1","viajeros","personas"]):
                self.state["travelers"] = text

    # =========================
    # Generar respuesta
    # =========================
    def generate_response(self, user_input: str) -> str:
        self._update_state_from_input(user_input)

        # Revisar campos faltantes
        missing = self._missing_fields()
        if missing:
            next_field = missing[0]
            questions = {
                "destination": "¿A qué destino te gustaría viajar?",
                "budget": "¿Cuál es tu presupuesto aproximado para este viaje?",
                "dates": "¿Cuáles son tus fechas de viaje?",
                "travelers": "¿Cuántas personas viajarán?",
                "interests": "¿Qué tipo de actividades o experiencias te interesan?",
                "constraints": "¿Tienes alguna restricción o requerimiento especial?",
            }
            return questions.get(next_field, "Por favor proporcióname más detalles del viaje.")

        # Todos los datos completos: generar itinerario
        planning_prompt = f"""
        Eres una Agencia de Viajes AI. Crea un itinerario detallado basado en:
        Destino: {self.state['destination']}
        Presupuesto: {self.state['budget']}
        Fechas: {self.state['dates']}
        Viajeros: {self.state['travelers']}
        Intereses: {self.state['interests']}
        Restricciones: {self.state['constraints']}
        """

        response = self.chat.send_message(planning_prompt)
        self.history.append({"role": "agent", "content": response.text})
        return response.text
