from pathlib import Path
from typing import List
from control_plane import StepTrace

class Visualizer:
    """Generates Mermaid diagrams to visualize the agentic workflow."""

    @staticmethod
    def generate_mermaid(steps: List[StepTrace]) -> str:
        """
        Generates a Mermaid sequence diagram showing the handoff between agents.
        """
        mermaid = ["graph TD", "    User((User Objective)) --> Phase1"]
        
        # 1. Flow Diagram (Phase to Phase)
        for i, step in enumerate(steps):
            phase_id = f"Phase{i+1}"
            next_phase_id = f"Phase{i+2}"
            
            # Clean label
            label = f"{step.phase_name}\n({step.agent_role})"
            mermaid.append(f'    {phase_id}["{label}"]')
            
            if i < len(steps) - 1:
                mermaid.append(f"    {phase_id} --> {next_phase_id}")

        # 2. Sequence Diagram (Handoffs)
        sequence = ["sequenceDiagram", "    actor User"]
        
        last_agent = "User"
        for step in steps:
            current_agent = step.agent_role.split('—')[0].strip() # Extract persona
            # Use short name for diagram actors
            actor_id = "".join([c for c in current_agent if c.isalnum()])
            
            sequence.append(f"    participant {actor_id} as {current_agent}")
            sequence.append(f"    {last_agent}->>+ {actor_id}: Passes Baton ({step.phase_name})")
            
            if step.gate_decision:
                status = "PASS" if step.gate_decision == "PASS" else "FAIL"
                sequence.append(f"    Note right of {actor_id}: Gate Result: {status}")
            
            sequence.append(f"    {actor_id}-->>- {last_agent}: Artifact Saved")
            # For simplicity, we keep baton passing relative to User or previous
            # But true waterfall is last -> next.
            # last_agent = actor_id 

        full_md = "\n## 📊 Visual Traceability\n\n"
        full_md += "### Phase Flow\n```mermaid\n" + "\n".join(mermaid) + "\n```\n\n"
        full_md += "### Agent Handoff Sequence\n```mermaid\n" + "\n".join(sequence) + "\n```\n"
        
        return full_md

    @staticmethod
    def append_to_report(report_path: str, mermaid_md: str):
        """Appends the Mermaid diagrams to the end of the report."""
        path = Path(report_path)
        if path.exists():
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n\n---\n")
                f.write(mermaid_md)
            return True
        return False
