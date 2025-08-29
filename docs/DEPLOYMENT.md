# Deployment Documentation

##  Overview

This document covers the deployment architecture, API endpoints, and implementation details for the AI Agents framework, with a focus on the Jenkins Agent deployment capabilities.

##  Architecture

### Deployment Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Agent         │    │   Jenkins       │
│   Web Server    │◄──►│   Processing    │◄──►│   Server        │
│   (Port 8000)   │    │   Engine        │    │   (Webhooks)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Tool Registry │    │   Notifications │
│   (Static Web)  │    │   (Jenkins +    │    │   (Email/Slack) │
│                 │    │   Notifications)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **FastAPI Server**: RESTful API and webhook endpoints
- **Agent Service**: Core agent processing and workflow execution
- **Jenkins Polling**: Real-time build monitoring service
- **Dashboard**: Web-based monitoring and control interface
- **Tool Registry**: Centralized tool management system

##  API Endpoints

### Core Agent Endpoints

#### List Available Agents
```http
GET /api/agents
```

**Response:**
```json
{
  "agents": [
    {
      "id": "jenkins_agent",
      "name": "Jenkins Agent",
      "description": "AI-powered Jenkins build monitoring and analysis",
      "status": "active",
      "version": "1.0.0"
    },
    {
      "id": "sales_assistant",
      "name": "Sales Assistant",
      "description": "Customer interaction and sales support agent",
      "status": "active",
      "version": "1.0.0"
    }
  ]
}
```

#### Get Agent Details
```http
GET /api/agents/{agent_id}
```

**Response:**
```json
{
  "id": "jenkins_agent",
  "name": "Jenkins Agent",
  "description": "AI-powered Jenkins build monitoring and analysis",
  "status": "active",
  "capabilities": [
    "build_monitoring",
    "failure_analysis",
    "auto_retry",
    "notifications"
  ],
  "supported_input_formats": ["webhook", "manual"],
  "output_channels": ["email", "slack"],
  "workflow_nodes": [
    "receive_webhook",
    "extract_job_data",
    "analyze_status",
    "handle_failure",
    "make_decision",
    "execute_action",
    "send_notifications"
  ]
}
```

#### Execute Agent
```http
POST /api/agents/{agent_id}/run
Content-Type: application/json
```

**Request Body:**
```json
{
  "input": {
    "job_name": "my-project",
    "build_number": 42,
    "status": "FAILURE",
    "jenkins_url": "http://jenkins.company.com"
  },
  "config": {
    "notifications": {
      "email": {"enabled": true},
      "slack": {"enabled": true}
    },
    "retry_settings": {
      "max_retries": 2
    }
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_12345",
  "status": "completed",
  "result": {
    "decision": "retry",
    "confidence": 0.85,
    "action_taken": "retriggered",
    "notification_sent": true,
    "analysis": {
      "cause": "Network timeout during dependency download",
      "category": "network",
      "suggested_actions": [
        "Retry build",
        "Check network connectivity",
        "Verify proxy settings"
      ]
    }
  },
  "execution_time": 12.5,
  "workflow_path": [
    "receive_webhook",
    "extract_job_data",
    "analyze_status",
    "handle_failure",
    "make_decision",
    "execute_action",
    "send_notifications"
  ]
}
```

#### Get Agent Status
```http
GET /api/agents/{agent_id}/status
```

**Response:**
```json
{
  "agent_id": "jenkins_agent",
  "status": "running",
  "last_execution": "2025-08-27T10:30:00Z",
  "total_executions": 156,
  "success_rate": 94.2,
  "average_execution_time": 8.3,
  "active_workflows": 2,
  "health_checks": {
    "jenkins_connectivity": "healthy",
    "llm_api": "healthy",
    "notifications": "healthy",
    "tool_registry": "healthy"
  }
}
```

### Jenkins-Specific Endpoints

#### Jenkins Webhook Endpoint
```http
POST /api/jenkins/webhook
Content-Type: application/json
```

**Request Body (Jenkins Notification Plugin format):**
```json
{
  "name": "my-project",
  "url": "job/my-project/",
  "build": {
    "full_url": "http://jenkins.company.com/job/my-project/42/",
    "number": 42,
    "phase": "FINALIZED",
    "status": "FAILURE",
    "url": "job/my-project/42/",
    "scm": {
      "url": "https://github.com/company/my-project.git",
      "branch": "main",
      "commit": "abc123"
    },
    "artifacts": {}
  }
}
```

**Response:**
```json
{
  "status": "accepted",
  "execution_id": "exec_12345",
  "message": "Webhook processed successfully",
  "agent_triggered": true
}
```

#### Jenkins Polling Status
```http
GET /api/jenkins/polling/status
```

**Response:**
```json
{
  "is_polling": true,
  "jenkins_url": "http://jenkins.company.com",
  "jenkins_user": "automation",
  "jenkins_connected": true,
  "poll_interval": 5,
  "known_jobs": 15,
  "monitored_builds": 3,
  "last_poll": "2025-08-27T10:29:45Z",
  "known_last_builds": {
    "my-project": 42,
    "other-project": 15,
    "test-project": 8
  },
  "current_monitored_builds": [
    "my-project#42",
    "other-project#16",
    "test-project#9"
  ]
}
```

#### Start/Stop Jenkins Polling
```http
POST /api/jenkins/polling/start
POST /api/jenkins/polling/stop
```

**Response:**
```json
{
  "status": "started",
  "message": "Jenkins polling service started",
  "poll_interval": 5
}
```

### Dashboard Endpoints

#### Dashboard Status
```http
GET /api/dashboard/status
```

**Response:**
```json
{
  "system_status": "healthy",
  "uptime": "2d 14h 32m",
  "active_agents": 2,
  "total_executions_today": 47,
  "current_load": "low",
  "memory_usage": "45%",
  "jenkins_connectivity": "connected",
  "recent_activities": [
    {
      "timestamp": "2025-08-27T10:29:00Z",
      "agent": "jenkins_agent",
      "action": "build_retry",
      "job": "my-project",
      "build": 42,
      "status": "success"
    }
  ]
}
```

#### Agent Metrics
```http
GET /api/dashboard/metrics
```

**Response:**
```json
{
  "jenkins_agent": {
    "executions_last_24h": 32,
    "success_rate": 94.2,
    "average_response_time": 8.3,
    "failures_analyzed": 18,
    "builds_retried": 5,
    "notifications_sent": 32,
    "top_failure_categories": [
      {"category": "dependency", "count": 8},
      {"category": "network", "count": 5},
      {"category": "syntax", "count": 3}
    ]
  },
  "system": {
    "cpu_usage": 35.2,
    "memory_usage": 45.8,
    "disk_usage": 23.1,
    "network_io": "12 MB/s"
  }
}
```

##  Configuration

### Environment Configuration

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Jenkins Configuration
JENKINS_URL=http://jenkins.company.com:8080
JENKINS_USER=automation-user
JENKINS_TOKEN=your-jenkins-api-token

# AI/LLM Configuration
OPENAI_API_KEY=your-openai-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
OPENAI_API_BASE=https://api.openai.com/v1

# Database Configuration (Optional)
DATABASE_URL=postgresql://user:password@localhost/agents_db
REDIS_URL=redis://localhost:6379

# Notification Configuration
EMAIL_SENDER=noreply@company.com
EMAIL_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Security Configuration
CORS_ORIGINS=["http://localhost:3000", "https://dashboard.company.com"]
API_RATE_LIMIT=100/minute
WEBHOOK_SECRET=your-webhook-secret
```

### Application Configuration

```python
# config/deployment.py
DEPLOYMENT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 4,
        "timeout": 300
    },
    "polling": {
        "jenkins": {
            "enabled": True,
            "interval": 5,
            "max_workers": 8
        }
    },
    "agents": {
        "jenkins_agent": {
            "max_concurrent_executions": 10,
            "timeout": 300,
            "retry_on_failure": True
        }
    },
    "logging": {
        "level": "INFO",
        "format": "json",
        "file": "logs/agents.log"
    }
}
```

## Monitoring & Observability

### Health Checks
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-27T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "jenkins": "healthy",
    "ai_api": "healthy"
  }
}
```

### Metrics Endpoint
```http
GET /metrics
```

Returns Prometheus-compatible metrics:
```
# HELP agent_executions_total Total number of agent executions
# TYPE agent_executions_total counter
agent_executions_total{agent="jenkins_agent",status="success"} 1425
agent_executions_total{agent="jenkins_agent",status="failure"} 87

# HELP agent_execution_duration_seconds Time spent executing agents
# TYPE agent_execution_duration_seconds histogram
agent_execution_duration_seconds_bucket{agent="jenkins_agent",le="5"} 234
agent_execution_duration_seconds_bucket{agent="jenkins_agent",le="10"} 1156
```

### Logging Configuration
```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/agents.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "ai_agents": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}
```
---

For detailed Jenkins Agent documentation, see [Jenkins Agent Documentation](JENKINS_AGENT.md).
For general framework information, see [Main README](../README.md).
