Analyze the following Jenkins build logs for job=$job_name build=#$build_number.

**Build Information:**
- Job: $job_name
- Build Number: $build_number
- Status: $build_status
- Timestamp: $timestamp

**Task:** 
Analyze the console logs to identify the root cause of the build failure and provide actionable recommendations.

**Required JSON Response Format:**
Return ONLY a valid JSON object with these exact keys:
{
  "cause": "Brief description of the root cause",
  "suggested_actions": ["Action 1", "Action 2", "Action 3"],
  "confidence": 0.85,
  "category": "network|dependency|syntax|configuration|resource|permission|unknown"
}

**Categories Explained:**
- **network**: Connection issues, timeouts, DNS problems
- **dependency**: Missing packages, import errors, version conflicts
- **syntax**: Code syntax errors, compilation failures
- **configuration**: Environment variables, config files, settings
- **resource**: Memory, disk space, CPU limitations
- **permission**: Access denied, file permissions, credentials
- **unknown**: Unclear cause requiring investigation

**Analysis Guidelines:**
1. Look for the ACTUAL error at the end of the logs, not just the beginning
2. Focus on Python runtime errors, exceptions, import errors
3. Identify missing dependencies or files
4. Check for configuration and connection issues
5. Set confidence based on how clear the error pattern is

**Console Logs:**
$console_logs
