# Jenkins Agent Documentation

##  Overview

The Jenkins Agent is a sophisticated AI-powered automation agent that monitors Jenkins builds, analyzes failures and successes, makes intelligent decisions about build actions, and sends notifications through multiple channels.

##  Key Features

###  Intelligent Build Analysis
- **Failure Analysis**: AI-powered analysis of build failures using LLM
- **Success Analysis**: Automated Jenkinsfile review with improvement suggestions
- **Log Sanitization**: Secure handling of sensitive data in build logs
- **Multi-pattern Detection**: Recognizes network issues, dependency problems, syntax errors, etc.

###  Automated Decision Making
- **Smart Retry Logic**: Automatically retries builds based on failure analysis
- **Investigation Routing**: Escalates complex issues for human investigation
- **Confidence Scoring**: Provides confidence levels for all decisions
- **Context-aware Actions**: Considers build history and patterns

###  Multi-channel Notifications
- **Email Notifications**: Rich HTML emails with detailed analysis
- **Slack Integration**: Real-time notifications with formatted messages
- **Template System**: Customizable notification templates
- **Status Updates**: Comprehensive status reporting

###  Security & Compliance
- **Log Sanitization**: Automatic redaction of sensitive information
- **PII Detection**: Advanced personally identifiable information detection
- **Environment Variables**: Secure credential management
- **Configurable Privacy**: Granular control over data handling

##  Architecture

### Workflow-Based Design
The Jenkins Agent follows a graph-based workflow with the following nodes:

```
receive_webhook → extract_job_data → analyze_status → handle_success/failure
                                                    → make_decision
                                                    → execute_action
                                                    → format_notification
                                                    → send_notifications
                                                    → end_process
```

### Tool Registry Integration
- **JenkinsWrapper**: Unified interface for Jenkins API operations
- **NotificationsWrapper**: Multi-channel notification management
- **Modular Design**: Easy to extend with new tools and capabilities

##  Configuration

### Environment Variables

```bash
# Jenkins Configuration
JENKINS_URL="http://localhost:8080"
JENKINS_USER="your-username"
JENKINS_TOKEN="your-api-token"

# AI/LLM Configuration
OPENAI_API_KEY="your-openai-key"
OPENROUTER_API_KEY="your-openrouter-key"  # Alternative to OpenAI

# Email Configuration
EMAIL_SENDER="notifications@yourcompany.com"
EMAIL_PASSWORD="your-app-password"
EMAIL_TO="devops@yourcompany.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587

# Slack Configuration
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Security Configuration
JENKINS_SANITIZE_LOGS=true
JENKINS_ENABLE_ADVANCED_PII=false
```


##  Workflow Details

### 1. Webhook Reception (`receive_webhook`)
- Validates incoming webhook payload
- Supports multiple webhook formats
- Extracts job name, build number, and metadata

### 2. Data Extraction (`extract_job_data`)
- Retrieves complete build information from Jenkins
- Downloads console logs with sanitization
- Extracts Jenkinsfile content from SCM
- Gathers build metadata and node information

### 3. Status Analysis (`analyze_status`)
- Routes to appropriate handler based on build status
- Supports SUCCESS, FAILURE, and other statuses
- Determines next workflow step

### 4. Failure Handling (`handle_failure`)
```python
# Example failure analysis output
{
  "cause": "Python import error: ModuleNotFoundError",
  "category": "dependency",
  "confidence": 0.85,
  "suggested_actions": [
    "Install missing Python dependencies",
    "Check requirements.txt file",
    "Verify virtual environment setup"
  ]
}
```

### 5. Success Handling (`handle_success`)
```python
# Example success analysis output
{
  "summary": "Build completed successfully with good practices",
  "improvements": [
    "Add timeout configuration to pipeline",
    "Implement parallel stages for testing",
    "Add build caching for dependencies"
  ],
  "confidence": 0.92
}
```

### 6. Decision Making (`make_decision`)
- AI-powered decision engine
- Considers failure patterns, build history, and confidence levels
- Supports decisions: `retry`, `investigate`, `notify`

### 7. Action Execution (`execute_action`)
- Executes decided actions (retry builds)
- Tracks retry attempts and limits
- Provides detailed execution logging

### 8. Notification Formatting (`format_notification`)
- Creates rich, contextual notifications
- Supports template-based formatting
- Includes analysis results and action details

### 9. Multi-channel Delivery (`send_notifications`)
- Sends notifications via configured channels
- Handles delivery failures gracefully
- Provides delivery status reporting

## 🛠️ Usage Examples

### Basic Usage (API)
```bash
# Trigger agent via webhook
curl -X POST http://localhost:8000/api/jenkins/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "my-project",
    "build_number": 42,
    "status": "FAILURE",
    "jenkins_url": "http://jenkins.company.com"
  }'
```

### CLI Usage
```bash
# Run agent directly
python run_cli.py jenkins_agent --input-file .\input.json
```

### Deployment Mode
```bash
python src/ai_agents/deployment/api_agent/start_api.py
```

##  Monitoring & Observability

### Logging
- Structured logging with contextual information
- Configurable log levels and formats
- Integration with external logging systems

### Metrics
- Build processing time
- Decision accuracy tracking
- Notification delivery rates
- Error rates and patterns

### Health Checks
- Jenkins connectivity status
- LLM API availability
- Notification channel health
- Tool registry status

## 🔧 Customization

### Custom Notification Templates
```jinja2
<!-- prompts/notification_template.tpl -->
 **Jenkins Build Failed**

**Job**: {{job_name}}
**Build**: #{{build_number}}
**Status**: {{build_status}}

**Analysis**:
{{analysis_summary}}

**Recommended Action**: {{decision}}
**Confidence**: {{confidence}}%
```

### Tool Extensions
```python
# Create custom tools in tools/ directory
class CustomJenkinsAnalyzer(BaseTool):
    @property
    def name(self) -> str:
        return "custom_analyzer"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Custom analysis logic
        return {"analysis": "custom_result"}
```


## Dashboard Screenshots

![Dashboard Screenshot 1](Screenshot%202025-08-27%20172056.png)
![Dashboard Screenshot 2](Screenshot%202025-08-27%20172115.png)


##  Troubleshooting

### Common Issues

#### 1. Connection Problems
```bash
# Check Jenkins connectivity
curl -u username:token http://jenkins-url/api/json

# Verify environment variables
echo $JENKINS_URL
echo $JENKINS_USER
```

#### 2. Authentication Errors
- Ensure Jenkins API token is valid
- Check user permissions for job access
- Verify CSRF protection settings

#### 3. LLM API Issues
- Validate API keys and quotas
- Check rate limiting settings
- Monitor API response times

#### 4. Notification Failures
- Test email SMTP configuration
- Verify Slack webhook URL
- Check firewall and network settings


## Performance

### Optimization Tips
1. **Log Sanitization**: Disable in development for faster processing
2. **API Caching**: Use Redis for caching Jenkins API responses
3. **Parallel Processing**: Enable concurrent webhook processing
4. **Retry Logic**: Configure appropriate retry delays

### Scaling Considerations
- Horizontal scaling with multiple agent instances
- Load balancing for webhook endpoints
- Database for state persistence
- Message queues for high-volume processing

##  Contributing


### Adding Features
1. Create feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit pull request

##  License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

For deployment information, see [Deployment Documentation](DEPLOYMENT.md).
For API details, see [API Documentation](../src/ai_agents/deployment/api_agent/README.md).
