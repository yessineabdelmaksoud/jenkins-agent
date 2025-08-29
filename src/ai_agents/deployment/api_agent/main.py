"""FastAPI application for AI Agents deployment."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os
import sys 
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from ai_agents.deployment.api_agent.api.routes import agents
from ai_agents.deployment.api_agent.core.config import get_settings
from ai_agents.deployment.api_agent.core.logging import setup_logging
from ai_agents.deployment.api_agent.services.jenkins_polling import JenkinsPollingService
from ai_agents.deployment.api_agent.services.agent_service import AgentService


# Global services
jenkins_polling_service: JenkinsPollingService = None
agent_service: AgentService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global jenkins_polling_service, agent_service
    
    # Startup
    setup_logging()
    settings = get_settings()
    
    # Initialize services
    agent_service = AgentService()
    
    # Start Jenkins polling service if enabled
    if settings.JENKINS_POLLING_ENABLED:
        jenkins_polling_service = JenkinsPollingService(
            poll_interval=settings.JENKINS_POLLING_INTERVAL
        )
        
        # Start polling in background task (non-blocking)
        await jenkins_polling_service.start_polling()
        print(f"🔄 Jenkins polling service started (interval: {settings.JENKINS_POLLING_INTERVAL}s)")
    else:
        print("⏸️ Jenkins polling service disabled")
    
    yield
    
    # Shutdown
    if jenkins_polling_service:
        await jenkins_polling_service.stop_polling()
        print("🛑 Jenkins polling service stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Agents API",
        description="API for managing and executing AI agents",
        version="1.0.0",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(agents.router, prefix="/api", tags=["agents"])
    
    # Mount static files for dashboard
    dashboard_path = Path(__file__).parent / "dashboard"
    if dashboard_path.exists():
        app.mount("/static", StaticFiles(directory=str(dashboard_path)), name="static")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "AI Agents API", "version": "1.0.0", "dashboard": "/dashboard"}

   
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        dashboard_file = Path(__file__).parent / "dashboard" / "index.html"
        if dashboard_file.exists():
            return FileResponse(str(dashboard_file), media_type="text/html")
        raise HTTPException(status_code=404, detail="Dashboard not found")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
