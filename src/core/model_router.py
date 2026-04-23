import os
from rich.console import Console

class ModelRouter:
    """Dynamically routes tasks to the most efficient/capable local model."""

    def __init__(self, console: Console = None):
        self.console = console or Console()
        
        # Configuration - Can be moved to .env or a YAML config
        self.large_reasoning_model = os.getenv("MODEL_REASONING", "qwen/qwen3.6-35b-a3b")
        self.coding_model = os.getenv("MODEL_CODER", "qwen2.5-coder-32b")
        self.small_fast_model = os.getenv("MODEL_FAST", "qwen2.5-7b-instruct")

    def route(self, task_type: str, phase_name: str = "") -> str:
        """
        Returns the best model name for the given task.
        task_types: 'reasoning', 'coding', 'summary', 'gate'
        """
        model = self.large_reasoning_model # Default
        
        if task_type == "coding" or "backend" in phase_name.lower() or "frontend" in phase_name.lower():
            model = self.coding_model
            self.console.print(f"  🎯 [dim]Router: Selected CODING model for {phase_name}[/dim]")
        elif task_type == "gate" or "review" in phase_name.lower() or "architecture" in phase_name.lower():
            model = self.large_reasoning_model
            self.console.print(f"  🎯 [dim]Router: Selected REASONING model for {phase_name}[/dim]")
        elif task_type == "summary" or "requirements" in phase_name.lower():
            model = self.small_fast_model
            self.console.print(f"  🎯 [dim]Router: Selected FAST model for {phase_name}[/dim]")
            
        return model

if __name__ == "__main__":
    router = ModelRouter()
    print(f"Backend Routing: {router.route('coding', 'Phase 3 Backend')}")
    print(f"Gate Routing: {router.route('gate', 'Architecture Review')}")
    print(f"Summary Routing: {router.route('summary', 'Phase 1 Requirements')}")
