import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY no encontrada en .env")

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

    def _missing_fields(self):
        return [k for k, v in self.state.items() if not v]

    def _update_state_from_input(self, text):
        # Aquí podrías usar extracción con regex o el propio modelo
        # Ejemplo básico de asignación manual (puedes mejorar)
        text_lower = text.lower()
        if "bolivianos" in text_lower or "$" in text_lower:
            self.state["budget"] = text
        if "enero" in text_lower or "julio" in text_lower:
            self.state["dates"] = text
        if "santa cruz" in text_lower:
            self.state["destination"] = "Santa Cruz"
        # Intereses genéricos
        if any(word in text_lower for word in ["cultura", "gastronomía", "naturaleza", "todo"]):
            self.state["interests"] = text
        if any(word in text_lower for word in ["persona", "adulto", "niño", "2", "1"]):
            self.state["travelers"] = text

    def generate_response(self, user_input: str) -> str:
        self._update_state_from_input(user_input)
        missing = self._missing_fields()

        if missing:
            # Pregunta solo el siguiente dato faltante
            next_field = missing[0]
            question_map = {
                "destination": "¿A qué destino te gustaría viajar?",
                "budget": "¿Cuál es tu presupuesto aproximado para este viaje?",
                "dates": "¿Cuáles son tus fechas de viaje?",
                "travelers": "¿Cuántas personas viajarán?",
                "interests": "¿Qué tipo de actividades o experiencias te interesan?",
                "constraints": "¿Tienes alguna restricción o requerimiento especial?",
            }
            return question_map.get(next_field, "Por favor proporcióname más detalles del viaje.")

        # Si ya tenemos todos los datos, generar itinerario
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
        return response.text
