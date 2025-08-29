Review the following Jenkins Declarative Pipeline (Jenkinsfile) for best practices and optimization opportunities.

**Build Information:**
- Job: $job_name
- Build Number: $build_number
- Status: $build_status (SUCCESS)

**Task:**
Analyze the Jenkinsfile and provide concrete improvement suggestions focusing on best practices, performance, security, and maintainability.

**Required JSON Response Format:**
Return ONLY a valid JSON object with these exact keys:
{
  "summary": "Brief overview of the pipeline analysis",
  "improvements": [
    "Specific improvement suggestion 1",
    "Specific improvement suggestion 2", 
    "Specific improvement suggestion 3"
  ],
  "confidence": 0.90
}

**Focus Areas for Analysis:**
1. **Best Practices**: Proper stage structure, agent configuration, options usage
2. **Performance**: Caching strategies, parallel execution, workspace cleanup
3. **Security**: Credentials handling, secrets management, input validation
4. **Maintainability**: Code organization, error handling, timeouts
5. **Reliability**: Retry mechanisms, health checks, notifications

**Improvement Categories to Consider:**
- Add missing `timeout` directives for long-running stages
- Implement proper `retry` strategies for flaky operations
- Add `parallel` blocks for independent stages
- Use `cache` or `stash`/`unstash` for dependencies
- Improve error handling with `catchError` or `try-catch`
- Add proper `post` actions for cleanup
- Use `when` conditions for conditional execution
- Implement proper artifact archiving
- Add health checks and monitoring

**Jenkinsfile Content:**
$jenkinsfile_content
