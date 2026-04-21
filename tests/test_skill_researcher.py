import sys
import os
import yaml
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def test_skill_researcher_evolution():
    from core.skill_researcher import SkillResearcher
    
    mock_console = MagicMock()
    policy_path = ".asd/policies/agent_rbac_test.yaml"
    
    # Ensure directory exists
    os.makedirs(".asd/policies", exist_ok=True)
    
    # Setup test policy
    initial_policy = {"agents": {"Phase 1": {"identity": "Engineer"}}}
    with open(policy_path, "w") as f:
        yaml.dump(initial_policy, f)
        
    sr = SkillResearcher(mock_console, policy_path=policy_path)
    
    # Mocking a [GAP_FOUND] response
    mock_response = """
    [GAP_FOUND]
    Specialized Role Name: "Phase 3.5 Database Optimizer"
    YAML:
    identity: "Database Tuning Expert"
    allowed_tools: ["delegate_to_qwen_agent", "execute_bash_command"]
    alignment: ["focus_on_index_optimization"]
    """
    
    with patch('core.skill_researcher.delegate_to_qwen_agent') as mock_delegate, \
         patch('subprocess.run') as mock_run:
        mock_delegate.return_value = {"output": mock_response}
        mock_run.return_value = MagicMock(returncode=0)
        
        evolved = sr.analyze_and_evolve("Needs high-performance SQL")
        
        assert evolved is True
        
        # Verify git commands were called
        # 1. checkout -b
        # 2. add
        # 3. commit
        assert mock_run.call_count == 3
        
        # Check branch name logic
        args, kwargs = mock_run.call_args_list[0]
        assert "evolution/add-phase-3-5-database-optimizer" in args[0]
        
        # Verify policy file was updated
        with open(policy_path, "r") as f:
            updated_policy = yaml.safe_load(f)
            
        assert "Phase 3.5 Database Optimizer" in updated_policy["agents"]
        
    print("✅ SkillResearcher Evolution Test Passed!")
    
    # Cleanup
    if os.path.exists(policy_path):
        os.remove(policy_path)

if __name__ == "__main__":
    try:
        test_skill_researcher_evolution()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
