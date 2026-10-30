"""Tests pour l'API AI Agents."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
import sys
from pathlib import Path
 
# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from ai_agents.deployment.api_agent.main import app
from ai_agents.deployment.api_agent.api.routes.agents import get_agent_service
from ai_agents.deployment.api_agent.services.agent_service import AgentService


@pytest.fixture
def client():
    """Fixture pour le client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Service d'agent mocké, injecté à la place de la dépendance FastAPI.

    Les routes reçoivent le service via Depends(get_agent_service) : patcher le
    module ne suffit pas, il faut passer par app.dependency_overrides.
    """
    service = Mock(spec=AgentService)
    app.dependency_overrides[get_agent_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_agent_service, None)


class TestAgentsEndpoints:
    """Tests pour les endpoints des agents."""
    
    def test_health_check(self, client):
        """Test du health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, client):
        """Test de l'endpoint racine."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_list_agents_success(self, mock_service, client):
        """Test de la liste des agents - succès."""
        mock_service.list_agents = AsyncMock(return_value=[
            {
                "id": "sales_assistant",
                "name": "Sales Assistant",
                "type": "sales_assistant",
                "description": "Test agent",
                "version": "1.0.0",
                "status": "idle"
            }
        ])

        response = client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert data["total"] >= 0
    
    def test_get_agent_details_success(self, mock_service, client):
        """Test des détails d'agent - succès."""
        mock_service.get_agent_details = AsyncMock(return_value={
            "id": "sales_assistant",
            "name": "Sales Assistant",
            "type": "sales_assistant",
            "description": "Test agent",
            "version": "1.0.0",
            "status": "idle",
            "config": {
                "workflow": {},
                "state_schema": {},
                "memory": None,
                "model": None
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        })

        response = client.get("/api/agents/sales_assistant")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sales_assistant"
    
    def test_get_agent_details_not_found(self, mock_service, client):
        """Test des détails d'agent - non trouvé."""
        mock_service.get_agent_details = AsyncMock(return_value=None)

        response = client.get("/api/agents/nonexistent")
        assert response.status_code == 404
    
    def test_get_agent_config_success(self, mock_service, client):
        """Test de la configuration d'agent - succès."""
        mock_service.get_agent_config = AsyncMock(return_value={
            "workflow": {"entrypoint": "start"},
            "state_schema": {"query": "string"},
            "memory": None,
            "model": {"type": "openai"}
        })

        response = client.get("/api/agents/sales_assistant/config")
        assert response.status_code == 200
        data = response.json()
        assert "workflow" in data
    
    def test_run_agent_success(self, mock_service, client):
        """Test d'exécution d'agent - succès."""
        mock_service.agent_exists = AsyncMock(return_value=True)
        mock_service.execute_agent = AsyncMock(return_value=None)

        payload = {
            "input_data": {"customer_query": "Test query"},
            "timeout": 60
        }
        
        response = client.post("/api/agents/sales_assistant/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert "agent_id" in data
        assert data["agent_id"] == "sales_assistant"
        assert data["status"] == "running"
        mock_service.execute_agent.assert_awaited_once()

    def test_run_agent_not_found(self, mock_service, client):
        """Test d'exécution d'agent - agent non trouvé."""
        mock_service.agent_exists = AsyncMock(return_value=False)

        payload = {"input_data": {"query": "test"}}
        
        response = client.post("/api/agents/nonexistent/run", json=payload)
        assert response.status_code == 404
    
    def test_get_agent_status_success(self, mock_service, client):
        """Test du statut d'agent - succès."""
        mock_service.agent_exists = AsyncMock(return_value=True)
        mock_service.get_agent_status = AsyncMock(side_effect=lambda agent_id, run_id: {
            "agent_id": agent_id,
            "run_id": run_id,
            "status": "idle",
            "last_activity": None,
            "current_run": None
        })

        response = client.get("/api/agents/sales_assistant/status")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "sales_assistant"
        assert "status" in data


class TestAgentService:
    """Tests pour le service d'agents."""
    
    def test_list_agents(self):
        """Test de la liste des agents."""
        service = AgentService()
        agents = asyncio.run(service.list_agents())
        assert isinstance(agents, list)
        # Vérifier qu'au moins un agent est disponible
        assert len(agents) > 0
    
    def test_agent_exists(self):
        """Test de vérification d'existence d'agent."""
        service = AgentService()
        
        # Test avec un agent existant
        exists = asyncio.run(service.agent_exists("sales_assistant"))
        assert exists is True
        
        # Test avec un agent inexistant
        exists = asyncio.run(service.agent_exists("nonexistent_agent"))
        assert exists is False
    
    def test_get_agent_details(self):
        """Test des détails d'agent."""
        service = AgentService()
        
        # Test avec un agent existant
        details = asyncio.run(service.get_agent_details("sales_assistant"))
        assert details is not None
        assert details.id == "sales_assistant"
        assert hasattr(details, 'config')
        
        # Test avec un agent inexistant
        details = asyncio.run(service.get_agent_details("nonexistent_agent"))
        assert details is None
    
    def test_get_agent_config(self):
        """Test de la configuration d'agent."""
        service = AgentService()
        
        # Test avec un agent existant
        config = asyncio.run(service.get_agent_config("sales_assistant"))
        assert config is not None
        assert hasattr(config, 'workflow')
        
        # Test avec un agent inexistant
        config = asyncio.run(service.get_agent_config("nonexistent_agent"))
        assert config is None

    def test_get_jenkins_agent_config(self):
        """La configuration du jenkins_agent (avec son bloc model) est valide."""
        service = AgentService()
        config = asyncio.run(service.get_agent_config("jenkins_agent"))
        assert config is not None
        assert config.workflow["entrypoint"] == "receive_webhook"
        assert config.model["model_id"] == "openai/gpt-3.5-turbo"


class TestErrorHandling:
    """Tests pour la gestion d'erreurs."""
    
    def test_invalid_json(self, client):
        """Test avec JSON invalide."""
        response = client.post(
            "/api/agents/sales_assistant/run",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, mock_service, client):
        """Test avec champs requis manquants."""
        mock_service.agent_exists = AsyncMock(return_value=True)
        mock_service.execute_agent = AsyncMock(return_value=None)
        # input_data a une valeur par défaut : le corps vide est accepté
        response = client.post("/api/agents/sales_assistant/run", json={})
        assert response.status_code == 200


if __name__ == "__main__":
    # Lancer les tests
    pytest.main([__file__, "-v"])
