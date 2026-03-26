import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class QwenClient:
    """
    A client wrapper to interface with the local qwen/qwen3-coder-next model
    running on LMStudio via the OpenAI compatibility layer.

    Supports extracting <think> reasoning blocks for the Control Plane.
    """
    def __init__(self):
        self.base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
        self.api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
        self.model_name = os.getenv("MODEL_NAME", "qwen/qwen3-coder-next")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    @staticmethod
    def _extract_reasoning(content: str) -> tuple[str, str]:
        """
        Splits the model output into (reasoning, output).
        Looks for <think>...</think> blocks that Qwen naturally produces.
        Falls back to returning empty reasoning if no block found.
        """
        think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)
        match = think_pattern.search(content)
        if match:
            reasoning = match.group(1).strip()
            output = think_pattern.sub("", content).strip()
            return reasoning, output
        return "", content.strip()

    def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
        """
        Send a request to the local Qwen model.
        
        Returns a structured dict:
        {
            "reasoning": str,   # The agent's thinking/reasoning chain
            "output": str,      # The final actionable output
            "raw": str,         # The complete unmodified response
        }
        """
        # Prepend instruction to expose reasoning in <think> blocks
        enhanced_system = (
            system_prompt + "\n\n"
            "IMPORTANT: Before producing your final output, wrap your internal reasoning "
            "in <think>...</think> tags. Show your goal decomposition, the sub-tasks you "
            "identified, which approach you chose, and why. Then produce your final output "
            "outside the tags."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": enhanced_system},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=4000
            )
            raw = response.choices[0].message.content
            reasoning, output = self._extract_reasoning(raw)
            return {
                "reasoning": reasoning,
                "output": output,
                "raw": raw,
            }
        except Exception as e:
            error_msg = f"Error communicating with local Qwen model: {str(e)}"
            return {
                "reasoning": "",
                "output": error_msg,
                "raw": error_msg,
            }

    def evaluate_gate(self, gate_name: str, objective: str, verification_context: str) -> dict:
        """
        Gatekeeper AI logic. Returns a structured dict with decision, reasoning, and trace.
        """
        system_prompt = f"""
You are the GATEKEEPER AI for the Agentic SDLC framework.
Your job is to evaluate if the current phase completed successfully based on the provided context.
You are evaluating Gate: {gate_name}

IMPORTANT: Before your final verdict, wrap your internal reasoning in <think>...</think> tags.
Show exactly which documents you reviewed, what criteria you checked, and how you reached your conclusion.

After your reasoning, RESPOND ONLY WITH A VALID JSON OBJECT matching this schema:
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            raw = response.choices[0].message.content
            thinking, json_part = self._extract_reasoning(raw)

            # Cleanup possible markdown JSON wrapping
            json_part = json_part.strip().lstrip("```json").rstrip("```").strip()
            result = json.loads(json_part)
            result["thinking"] = thinking
            return result
        except Exception as e:
            return {
                "decision": "FAIL",
                "reasoning": f"Exception occurred during Gatekeeper evaluation: {str(e)}",
                "thinking": "",
            }
