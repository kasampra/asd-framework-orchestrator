import time
from rich.console import Console
from rich.panel import Panel
from mcp_server import delegate_to_qwen_agent, evaluate_quality_gate

class BenchmarkingArena:
    """Sandbox for verifying new agent roles before framework integration."""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def run_smoke_test(self, role_name: str, role_data: dict) -> bool:
        """
        Runs a quick validation test for a proposed role.
        1. Agent generates code for a simple task.
        2. Gatekeeper verifies the code.
        """
        self.console.print(f"🏟️  [bold blue]Arena: Benchmarking new role '{role_name}'...[/bold blue]")
        
        challenge = "Write a Python function 'calculate_roi(investment, return_val)' that returns the percentage ROI."
        context = f"ROLE IDENTITY: {role_data.get('identity')}\nALIGNMENT: {', '.join(role_data.get('alignment', []))}"
        
        # 1. Generation Phase
        self.console.print(f"  ⚒️  [dim]Agent '{role_name}' is attempting the challenge...[/dim]")
        gen_result = delegate_to_qwen_agent(role_name, challenge, context)
        proposed_code = gen_result.get("output", "")
        
        # 2. Verification Phase
        self.console.print(f"  ⚖️  [dim]Gatekeeper is verifying the output...[/dim]")
        gate_objective = "The code must be valid Python, implement 'calculate_roi' correctly, and return a percentage."
        gate_result = evaluate_quality_gate("Benchmarking Gate", gate_objective, proposed_code)
        
        decision = gate_result.get("decision", "FAIL")
        reasoning = gate_result.get("reasoning", "No reasoning provided.")
        
        if decision == "PASS":
            self.console.print(f"✅ [bold green]Benchmark Passed![/bold green] Role '{role_name}' is viable.")
            return True
        else:
            self.console.print(f"❌ [bold red]Benchmark Failed:[/bold red] {reasoning}")
            return False

if __name__ == "__main__":
    # Test the Arena with a dummy role
    arena = BenchmarkingArena()
    dummy_role = {
        "identity": "ROI Optimization Expert",
        "alignment": ["mathematical precision", "clean code"]
    }
    arena.run_smoke_test("Test ROI Agent", dummy_role)
