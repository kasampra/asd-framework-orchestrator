import sys
import os
from unittest.mock import MagicMock, patch

# Mock the console and mcp_server before importing ReflectionManager
mock_console = MagicMock()
mock_mcp = MagicMock()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Create the test
def test_reflection_logic():
    from core.reflection import ReflectionManager
    
    rm = ReflectionManager(mock_console)
    
    phase_name = "Test Phase"
    objective = "Write a hello world script."
    initial_output = "print('hello')"
    context = "No context"

    # We expect 2 calls to delegate_to_qwen_agent:
    # 1. For reflection (critique)
    # 2. For refinement
    
    with patch('core.reflection.delegate_to_qwen_agent') as mock_delegate:
        # Mocking the critique response
        mock_delegate.side_effect = [
            {"output": "The output is too simple. Add a comment."}, # Critique
            {"output": "# Refined\nprint('hello')"} # Refined Output
        ]
        
        final_output = rm.reflect_and_refine(phase_name, objective, initial_output, context)
        
        # Assertions
        assert "Refined" in final_output
        assert mock_delegate.call_count == 2
        
        # Check first call (Reflection)
        args, kwargs = mock_delegate.call_args_list[0]
        assert "Reflection" in args[0]
        assert "Senior Technical Critic" in args[1]
        
        # Check second call (Refinement)
        args, kwargs = mock_delegate.call_args_list[1]
        assert "Refinement" in args[0]
        assert "critique" in args[1].lower()
        
    print("✅ Reflection Logic Test Passed!")

def test_reflection_perfect_skip():
    from core.reflection import ReflectionManager
    
    rm = ReflectionManager(mock_console)
    
    with patch('core.reflection.delegate_to_qwen_agent') as mock_delegate:
        # Mocking a 'PERFECT' critique
        mock_delegate.return_value = {"output": "PERFECT"}
        
        final_output = rm.reflect_and_refine("Phase", "Obj", "initial", "ctx")
        
        # Should return initial output directly
        assert final_output == "initial"
        assert mock_delegate.call_count == 1
        
    print("✅ Reflection 'PERFECT' Skip Test Passed!")

if __name__ == "__main__":
    try:
        test_reflection_logic()
        test_reflection_perfect_skip()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        sys.exit(1)
