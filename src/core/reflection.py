import os
from mcp_server import delegate_to_qwen_agent

class ReflectionManager:
    """Manages the 'Self-Critique' loop for agents before they hit the formal Gatekeeper."""
    
    def __init__(self, console):
        self.console = console

    def reflect_and_refine(self, phase_name: str, objective: str, initial_output: str, context: str) -> str:
        self.console.print(f"🔍 [bold magenta]Starting Self-Reflection for {phase_name}...[/bold magenta]")
        
        # 1. Generate Critique
        reflection_prompt = f"""
        You are a Senior Technical Critic. Review the following proposed output for the phase: {phase_name}.
        
        PHASE OBJECTIVE:
        {objective}
        
        PROPOSED OUTPUT:
        {initial_output}
        
        TASK:
        Identify any missing requirements, logical flaws, security risks, or code style violations. 
        Be brutal and concise. If it is perfect, say 'PERFECT'.
        """
        
        reflection_result = delegate_to_qwen_agent(
            f"{phase_name} Reflection", 
            reflection_prompt, 
            context
        )
        
        critique = reflection_result.get("output", "")
        self.console.print(f"🤔 [dim]Self-Critique: {critique[:200]}...[/dim]")
        
        if "PERFECT" in critique.upper() and len(critique) < 20:
            self.console.print("✨ [green]Output verified as perfect. Skipping refinement.[/green]")
            return initial_output

        # 2. Refine Output
        refinement_prompt = f"""
        You are the {phase_name} Agent. You previously generated an output, but a critic found issues.
        
        CRITIQUE:
        {critique}
        
        ORIGINAL OUTPUT:
        {initial_output}
        
        TASK:
        Rewrite the output to address the critic's feedback while still fulfilling the original objective.
        Ensure all files are correctly formatted in markdown code blocks.
        """
        
        refinement_result = delegate_to_qwen_agent(
            f"{phase_name} Refinement",
            refinement_prompt,
            context
        )
        
        refined_output = refinement_result.get("output", "")
        self.console.print("🚀 [bold green]Refinement complete! Procedural quality improved.[/bold green]")
        
        return refined_output
