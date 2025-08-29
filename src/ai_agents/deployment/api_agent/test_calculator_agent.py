"""Test script spécifique pour l'agent Calculator via l'API."""

import sys
import time
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from ai_agents.deployment.api_agent.examples.api_examples import AgentAPIClient


def test_calculator_agent():
    """Test complet de l'agent Calculator via l'API."""
    print("🧮 TEST DE L'AGENT CALCULATOR")
    print("=" * 50)
    
    client = AgentAPIClient()
    
    try:
        # Vérifier que l'API est accessible
        print("🔍 1. Vérification de l'API...")
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code != 200:
                print("❌ API non accessible. Démarrez-la avec:")
                print("   python src/ai_agents/deployment/api_agent/start_api.py")
                return False
            print("✅ API accessible")
        except Exception:
            print("❌ Impossible de se connecter à l'API")
            return False
        
        # Vérifier que l'agent calculator est disponible
        print("\n📋 2. Vérification de l'agent Calculator...")
        agents = client.list_agents()
        calculator_found = False
        for agent in agents['agents']:
            if agent['id'] == 'calculator':
                calculator_found = True
                print(f"✅ Agent Calculator trouvé: {agent['name']} ({agent['status']})")
                break
        
        if not calculator_found:
            print("❌ Agent Calculator non trouvé dans la liste des agents")
            print("Agents disponibles:", [a['id'] for a in agents['agents']])
            return False
        
        # Obtenir les détails de l'agent
        print("\n🔍 3. Détails de l'agent Calculator...")
        details = client.get_agent_details("calculator")
        print(f"   📝 Nom: {details['name']}")
        print(f"   🏷️  Type: {details['type']}")
        print(f"   📊 Statut: {details['status']}")
        print(f"   🔧 Workflow: {details['config']['workflow']['entrypoint']}")
        print(f"   🧠 Modèle: {details['config'].get('model', 'Aucun (pas d\'OpenAI requis)')}")
        
        # Tests de calculs simples
        test_expressions = [
            "2 + 3",
            "10 - 4",
            "5 * 6",
            "20 / 4",
            "(2 + 3) * 4",
            "2^3",
            "sqrt(16)",
            "abs(-5)",
            "3.14 * 2",
            "100 / 3"
        ]
        
        print(f"\n🧮 4. Tests de calculs ({len(test_expressions)} expressions)...")
        
        successful_tests = 0
        failed_tests = 0
        
        for i, expression in enumerate(test_expressions, 1):
            print(f"\n   Test {i}/{len(test_expressions)}: {expression}")
            
            try:
                # Lancer le calcul
                input_data = {"expression": expression}
                run_result = client.run_agent("calculator", input_data, timeout=30)
                run_id = run_result['run_id']
                
                print(f"      🆔 Run ID: {run_id[:8]}...")
                
                # Surveiller l'exécution
                max_attempts = 10
                final_result = None
                
                for attempt in range(max_attempts):
                    status = client.get_agent_status("calculator", run_id)
                    
                    if status.get('current_run'):
                        current_run = status['current_run']
                        current_status = current_run['status']
                        
                        if current_status == 'completed':
                            final_result = current_run.get('result', {})
                            print(f"      ✅ Résultat: {final_result.get('final_answer', 'N/A')}")
                            successful_tests += 1
                            break
                        elif current_status == 'failed':
                            error = current_run.get('error', 'Unknown error')
                            print(f"      ❌ Échec: {error}")
                            failed_tests += 1
                            break
                        elif current_status == 'running':
                            print(f"      ⏳ En cours... (tentative {attempt + 1})")
                    
                    time.sleep(0.5)
                else:
                    print(f"      ⏰ Timeout après {max_attempts} tentatives")
                    failed_tests += 1
                
            except Exception as e:
                print(f"      ❌ Erreur: {str(e)}")
                failed_tests += 1
        
        # Tests d'erreurs
        print(f"\n⚠️  5. Tests de gestion d'erreurs...")
        
        error_expressions = [
            "2 / 0",  # Division par zéro
            "invalid expression",  # Expression invalide
            "2 + + 3",  # Syntaxe incorrecte
            "",  # Expression vide
        ]
        
        for i, expression in enumerate(error_expressions, 1):
            print(f"\n   Test erreur {i}/{len(error_expressions)}: '{expression}'")
            
            try:
                input_data = {"expression": expression}
                run_result = client.run_agent("calculator", input_data, timeout=30)
                run_id = run_result['run_id']
                
                # Attendre le résultat
                time.sleep(2)
                status = client.get_agent_status("calculator", run_id)
                
                if status.get('current_run'):
                    current_run = status['current_run']
                    if current_run['status'] == 'failed' or 'Error' in str(current_run.get('result', {})):
                        print(f"      ✅ Erreur correctement gérée")
                    else:
                        print(f"      ⚠️  Erreur non détectée: {current_run.get('result')}")
                
            except Exception as e:
                print(f"      ✅ Exception correctement levée: {str(e)[:50]}...")
        
        # Statistiques finales
        print(f"\n📊 6. Statistiques finales:")
        print(f"   ✅ Tests réussis: {successful_tests}")
        print(f"   ❌ Tests échoués: {failed_tests}")
        print(f"   📈 Taux de réussite: {(successful_tests / len(test_expressions) * 100):.1f}%")
        
        # Lister toutes les exécutions
        print(f"\n📋 7. Historique des exécutions:")
        try:
            runs = client.list_agent_runs("calculator")
            print(f"   📊 Nombre total d'exécutions: {len(runs)}")
            
            if runs:
                print("   🕒 Dernières exécutions:")
                for run in runs[:5]:  # Afficher les 5 dernières
                    result_preview = str(run.get('result', {})).get('final_answer', 'N/A')[:30]
                    print(f"      • {run['run_id'][:8]}: {run['status']} - {result_preview}...")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la récupération de l'historique: {e}")
        
        print(f"\n🎉 TEST DE L'AGENT CALCULATOR TERMINÉ!")
        
        if successful_tests >= len(test_expressions) * 0.8:  # 80% de réussite
            print("✅ L'agent Calculator fonctionne correctement!")
            return True
        else:
            print("⚠️  L'agent Calculator a des problèmes de fonctionnement")
            return False
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculator_direct():
    """Test direct de l'agent Calculator (sans API)."""
    print("\n🔧 TEST DIRECT DE L'AGENT CALCULATOR (sans API)")
    print("-" * 50)
    
    try:
        from ai_agents.agents.calculator import CalculatorAgent
        
        # Charger l'agent
        agent = CalculatorAgent.load_config()
        calculator = CalculatorAgent(agent)
        
        # Test simple
        input_data = {"expression": "2 + 3 * 4"}
        result = calculator.run(input_data)
        
        print(f"✅ Test direct réussi!")
        print(f"   Expression: {input_data['expression']}")
        print(f"   Résultat: {result.get('final_answer', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test direct échoué: {e}")
        return False


if __name__ == "__main__":
    print("🧮 TESTS DE L'AGENT CALCULATOR")
    print("=" * 60)
    
    # Test via API
    api_success = test_calculator_agent()
    
    # Test direct
    direct_success = test_calculator_direct()
    
    print(f"\n📊 RÉSUMÉ DES TESTS:")
    print(f"   🌐 Test API: {'✅ Réussi' if api_success else '❌ Échoué'}")
    print(f"   🔧 Test direct: {'✅ Réussi' if direct_success else '❌ Échoué'}")
    
    if api_success and direct_success:
        print(f"\n🎊 TOUS LES TESTS RÉUSSIS!")
        print(f"🧮 L'agent Calculator est entièrement fonctionnel!")
    else:
        print(f"\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ") 
        if not api_success:
            print("💡 Vérifiez que l'API est démarrée")
        if not direct_success:
            print("💡 Vérifiez la configuration de l'agent")
    
    sys.exit(0 if (api_success and direct_success) else 1)
