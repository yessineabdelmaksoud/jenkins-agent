
"""Test script for Jenkins Agent"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_agents.agents.registry import get_agent
from ai_agents.utils.config_loader import load_env_vars

def test_jenkins_agent():
    """Test the Jenkins Agent with sample data"""
    
    # Load environment variables
    env_vars = load_env_vars()
    print(f"Environment loaded. OPENAI_API_KEY set: {bool(env_vars.get('OPENAI_API_KEY'))}")
    
    # Test data
    test_data = {
        'job_name': 'relancejob',
        'build_number': 33,
        'jenkins_url': 'http://localhost:8080',
        'build_status': 'SUCCESS'
    }
    
    print(f"Testing Jenkins Agent with data: {test_data}")
    print("-" * 50)
    
    try:
        # Get the agent
        agent = get_agent('jenkins_agent')
        print("✅ Agent loaded successfully")
        
        # Run the agent
        result = agent.run(test_data)
        print("✅ Agent execution completed")
        
        # Display results
        print("\n" + "=" * 50)
        print("JENKINS AGENT RESULTS")
        print("=" * 50)
        print(f"Job: {result.get('job_name')}")
        print(f"Build: #{result.get('build_number')}")
        print(f"Status: {result.get('build_status')}")
        print(f"Action taken: {result.get('action_taken', 'None')}")
        print(f"Next node: {result.get('next_node')}")
        
        # Show analysis if available
        analysis = result.get('success_analysis') or result.get('failure_analysis')
        if analysis:
            print(f"\nAnalysis: {analysis}")
            
        # Show notification content
        notification = result.get('notification_content')
        if notification:
            print(f"\nNotification: {notification}")
            
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_jenkins_agent()
