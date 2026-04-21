import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def test_orchestrator_integration():
    # Mocking external dependencies
    with patch('mcp_server.qwen'), \
         patch('mcp_server.load_agent_roles', return_value={}), \
         patch('mcp_server.load_agent_skills', return_value={}), \
         patch('mcp_server.load_instructions', return_value=""), \
         patch('mcp_server.delegate_to_qwen_agent') as mock_delegate, \
         patch('mcp_server.evaluate_quality_gate') as mock_gate:
        
        from orchestrator import execute_phase_with_resilience, ControlPlane
        from core.reflection import ReflectionManager
        
        cp = ControlPlane()
        mock_console = MagicMock()
        rm = ReflectionManager(mock_console)
        
        # Scenario:
        # 1. run_phase calls delegate_to_qwen_agent (once)
        # 2. ReflectionManager calls delegate_to_qwen_agent (twice: critique + refine)
        # 3. run_gate calls evaluate_quality_gate (once)
        
        mock_delegate.side_effect = [
            {"output": "initial"}, # run_phase
            {"output": "critique"}, # reflection critique
            {"output": "refined"}  # reflection refinement
        ]
        mock_gate.return_value = {"decision": "PASS", "reasoning": "Good"}
        
        output = execute_phase_with_resilience(
            cp,
            phase_name="Test",
            phase_objective="Obj",
            context="Ctx",
            gate_name="Gate",
            gate_objective="GObj",
            reflection_manager=rm
        )
        
        assert output == "refined"
        assert mock_delegate.call_count == 3
        assert mock_gate.call_count == 1
        
    print("✅ Orchestrator Integration Test Passed!")

if __name__ == "__main__":
    try:
        test_orchestrator_integration()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
