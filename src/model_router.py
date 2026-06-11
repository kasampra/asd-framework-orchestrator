import os

class ModelRouter:
    """
    ModelRouter routes LLM tasks to the appropriate model based on task type.
    Routes tasks to either a fast model (for reflection, content, summaries) 
    or a full model (for gates, complex code generation).
    """
    def __init__(self):
        # Default full model
        self.full_model = os.getenv("MODEL_NAME", "qwen/qwen3.6-35b-a3b")
        # Fast model, falling back to full model if not set
        self.fast_model = os.getenv("FAST_MODEL_NAME", self.full_model)

    def get_model(self, task_type: str) -> str:
        """
        Returns the model identifier for a given task type.
        Allowed task_types: 'gate', 'generation', 'reflection', 'healing', etc.
        """
        if task_type in ("reflection", "content", "summary"):
            return self.fast_model
        return self.full_model
