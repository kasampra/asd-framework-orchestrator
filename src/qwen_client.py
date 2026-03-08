import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class QwenClient:
    """
    A client wrapper to interface with the local qwen/qwen3-coder-next model
    running on LMStudio via the OpenAI compatibility layer.
    """
    def __init__(self):
        self.base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
        self.api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
        self.model_name = os.getenv("MODEL_NAME", "qwen/qwen3-coder-next")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """
        Send a request to the local Qwen model.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with local Qwen model: {str(e)}"

    def evaluate_gate(self, gate_name: str, objective: str, verification_context: str) -> dict:
        """
        Gatekeeper AI logic. Returns Pass/Fail based on the context provided.
        """
        system_prompt = f"""
You are the GATEKEEPER AI for the Agentic SDLC framework.
Your job is to evaluate if the current phase completed successfully based on the provided context.
You are evaluating Gate: {gate_name}

RESPOND ONLY WITH A VALID JSON OBJECT matching this schema:
{{
    "decision": "PASS" or "FAIL",
    "reasoning": "Detailed explanation of why it passed or failed, including specific tradeoffs or gaps identified."
}}
"""
        user_prompt = f"""
OBJECTIVE OF THIS PHASE:
{objective}

VERIFICATION CONTEXT (Agent Output / Evidence):
{verification_context}

Evaluate the evidence against the objective. Does it meet all criteria securely and correctly?
"""
        try:
            # We use JSON mode or enforce strict prompt compliance since it's a local model
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            # Cleanup possible markdown JSON wrapping
            content = content.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(content)
        except Exception as e:
            return {
                "decision": "FAIL",
                "reasoning": f"Exception occurred during Gatekeeper evaluation: {str(e)}"
            }
