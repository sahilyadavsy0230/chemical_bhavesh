# ============================================================
# app/ai/groq_client.py  —  Groq Llama-3 AI Integration
# ============================================================

import time
import logging
from typing import Optional
from flask import current_app

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)


class GroqAIClient:
    """
    Wrapper around the Groq API (Llama-3.3-70b-versatile).
    Provides methods for:
      - general chat (assistant)
      - design explanation
      - optimization suggestions
      - formula explanation
      - safety analysis
    """

    def __init__(self):
        self._client: Optional[object] = None

    def _get_client(self):
        """Lazy-initialise the Groq client using Flask app config."""
        if self._client is None:
            api_key = current_app.config.get('GROQ_API_KEY', '')
            if not api_key:
                raise ValueError('GROQ_API_KEY not configured. Add it to your .env file.')
            if not GROQ_AVAILABLE:
                raise ImportError('groq package not installed. Run: pip install groq')
            self._client = Groq(api_key=api_key)
        return self._client

    # ── Core Chat ────────────────────────────────────────────

    def chat(self, messages: list, temperature: float = 0.3,
             max_tokens: int = 2048) -> dict:
        """
        Send a conversation to Groq and return the response.

        Args:
            messages: List of {'role': 'user'|'assistant'|'system', 'content': str}
            temperature: Creativity (0=deterministic, 1=creative)
            max_tokens: Maximum response length

        Returns:
            {'content': str, 'tokens': int, 'response_time': float, 'error': None|str}
        """
        start = time.time()
        try:
            client = self._get_client()
            model  = current_app.config.get('GROQ_MODEL', 'llama-3.1-8b-instant')

            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = completion.choices[0].message.content
            tokens  = completion.usage.total_tokens if completion.usage else 0
            elapsed = round(time.time() - start, 3)

            return {'content': content, 'tokens': tokens,
                    'response_time': elapsed, 'error': None}

        except Exception as e:
            logger.error(f'Groq API error: {e}')
            return {
                'content': (
                    'I apologise — the AI assistant is temporarily unavailable. '
                    'Please check your GROQ_API_KEY in the .env file and try again.'
                ),
                'tokens': 0,
                'response_time': 0,
                'error': str(e),
            }

    # ── Specialised Methods ───────────────────────────────────

    def explain_calculation(self, equipment_type: str, results: dict) -> dict:
        """Explain what each calculated result means in plain language."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.explain_calculation_prompt(equipment_type, results)
        return self.chat(msgs, temperature=0.2)

    def suggest_optimization(self, equipment_type: str, inputs: dict,
                             results: dict) -> dict:
        """Generate AI optimization suggestions for a design."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.optimization_prompt(equipment_type, inputs, results)
        return self.chat(msgs, temperature=0.4)

    def explain_formula(self, formula_name: str, context: str = '') -> dict:
        """Explain a chemical engineering formula in detail."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.formula_explanation_prompt(formula_name, context)
        return self.chat(msgs, temperature=0.3)

    def safety_analysis(self, equipment_type: str, inputs: dict,
                        results: dict) -> dict:
        """Generate detailed industrial safety recommendations."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.safety_analysis_prompt(equipment_type, inputs, results)
        return self.chat(msgs, temperature=0.2)

    def debug_inputs(self, equipment_type: str, errors: list,
                     inputs: dict) -> dict:
        """Help user fix invalid inputs."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.debug_inputs_prompt(equipment_type, errors, inputs)
        return self.chat(msgs, temperature=0.3)

    def general_chat(self, user_message: str, history: list,
                     context: str = '') -> dict:
        """General-purpose engineering assistant chat."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.general_chat_prompt(user_message, history, context)
        return self.chat(msgs, temperature=0.5, max_tokens=1024)

    def material_recommendation(self, equipment_type: str, conditions: dict) -> dict:
        """Recommend construction materials based on process conditions."""
        from app.ai.prompts import PromptBuilder
        msgs = PromptBuilder.material_recommendation_prompt(equipment_type, conditions)
        return self.chat(msgs, temperature=0.3)
