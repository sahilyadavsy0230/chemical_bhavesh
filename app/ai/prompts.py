# ============================================================
# app/ai/prompts.py  —  Prompt Templates for Groq AI
# ============================================================
import json


SYSTEM_PROMPT = """You are ChemDesignAI — an expert chemical engineering assistant embedded 
in a professional process equipment design platform. You have deep knowledge of:
- Chemical engineering fundamentals (thermodynamics, fluid mechanics, heat/mass transfer)
- Equipment design (heat exchangers, reactors, distillation columns, pumps, compressors)
- Industry codes & standards (ASME, API, TEMA, OSHA, ATEX)
- Process safety & hazard analysis (HAZOP, LOPA)
- Economic evaluation (capital cost, operating cost, ROI)

Rules:
1. Always be concise but thorough — this is an engineering context.
2. Use SI units unless asked otherwise.
3. Cite equations with their source (e.g., "Dittus-Boelter, 1930").
4. When you identify issues, provide actionable fixes.
5. Format answers with clear headings and bullet points.
6. Never make up numerical values — state assumptions explicitly.
"""


class PromptBuilder:
    """Static factory methods to build Groq message lists."""

    @staticmethod
    def explain_calculation_prompt(equipment_type: str, results: dict) -> list:
        results_str = json.dumps(results, indent=2, default=str)
        return [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f"Please explain the following {equipment_type.replace('_',' ').title()} "
                f"design calculation results in plain language. For each key result, explain:\n"
                f"1. What it means physically\n"
                f"2. Whether the value is within typical industry ranges\n"
                f"3. How it affects the equipment performance\n\n"
                f"Results:\n{results_str}"
            )},
        ]

    @staticmethod
    def optimization_prompt(equipment_type: str, inputs: dict, results: dict) -> list:
        return [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f"Analyze this {equipment_type.replace('_',' ').title()} design and provide "
                f"specific optimization recommendations to:\n"
                f"1. Improve energy efficiency\n"
                f"2. Reduce capital cost\n"
                f"3. Improve operability & controllability\n"
                f"4. Suggest better operating conditions (temperature, pressure, flow)\n"
                f"5. Material selection improvements\n\n"
                f"Design Inputs: {json.dumps(inputs, default=str)}\n"
                f"Calculated Results: {json.dumps(results, default=str)}"
            )},
        ]

    @staticmethod
    def formula_explanation_prompt(formula_name: str, context: str) -> list:
        return [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f"Explain the '{formula_name}' equation used in chemical process design:\n"
                f"1. State the complete equation with all variables defined\n"
                f"2. Derive or explain where it comes from (physical basis)\n"
                f"3. State all assumptions and when it is valid\n"
                f"4. Provide a worked numerical example\n"
                f"5. List common errors when applying this equation\n"
                f"Context: {context}"
            )},
        ]

    @staticmethod
    def safety_analysis_prompt(equipment_type: str, inputs: dict, results: dict) -> list:
        return [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f"Perform an industrial safety analysis for this {equipment_type.replace('_',' ').title()} design:\n"
                f"1. Identify all major hazards (pressure, temperature, chemical, mechanical)\n"
                f"2. Recommend safety devices (PSV, rupture disc, interlocks)\n"
                f"3. Applicable codes & standards (ASME, API, OSHA, local regulations)\n"
                f"4. Maintenance & inspection intervals\n"
                f"5. Emergency shutdown procedure\n"
                f"6. Personal protective equipment (PPE) requirements\n\n"
                f"Design Inputs: {json.dumps(inputs, default=str)}\n"
                f"Results: {json.dumps(results, default=str)}"
            )},
        ]

    @staticmethod
    def debug_inputs_prompt(equipment_type: str, errors: list, inputs: dict) -> list:
        return [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f"A user entered inputs for a {equipment_type.replace('_',' ').title()} design "
                f"and got the following validation errors:\n"
                f"Errors: {json.dumps(errors)}\n"
                f"User Inputs: {json.dumps(inputs, default=str)}\n\n"
                f"Please:\n"
                f"1. Explain each error clearly in non-technical language\n"
                f"2. Provide the correct/recommended values with justification\n"
                f"3. Show typical industry ranges for each problematic parameter\n"
                f"4. Suggest a complete set of corrected inputs"
            )},
        ]

    @staticmethod
    def general_chat_prompt(user_message: str, history: list, context: str) -> list:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        # Add conversation history (last 10 turns max for token efficiency)
        for turn in history[-10:]:
            messages.append({'role': 'user',      'content': turn.get('user_message', '')})
            messages.append({'role': 'assistant',  'content': turn.get('ai_response', '')})
        if context:
            messages.append({
                'role': 'system',
                'content': f'Current design context: {context}'
            })
        messages.append({'role': 'user', 'content': user_message})
        return messages

    @staticmethod
    def material_recommendation_prompt(equipment_type: str, conditions: dict) -> list:
        return [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': (
                f"Recommend construction materials for a {equipment_type.replace('_',' ').title()} "
                f"under these process conditions:\n"
                f"{json.dumps(conditions, indent=2, default=str)}\n\n"
                f"For each recommended material provide:\n"
                f"1. Material name and grade (ASTM/ASME designation)\n"
                f"2. Why it is suitable for these conditions\n"
                f"3. Temperature and pressure limits\n"
                f"4. Corrosion resistance against the process fluid\n"
                f"5. Relative cost index (1=Carbon Steel baseline)\n"
                f"6. Any special fabrication requirements"
            )},
        ]
