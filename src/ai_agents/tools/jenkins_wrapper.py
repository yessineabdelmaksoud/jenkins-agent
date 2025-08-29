"""Wrapper for Jenkins tools to integrate with tool registry."""

import os
from typing import Dict, Any, Optional, List
from .base import BaseTool
from .jenkins.client import JenkinsClient


class JenkinsWrapper(BaseTool):
    """Wrapper for Jenkins client that integrates with tool registry."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Use environment variables as fallback
        self.jenkins_url = (config and config.get("jenkins_url")) or os.getenv("JENKINS_URL")
        self.username = (config and config.get("username")) or os.getenv("JENKINS_USER")
        self.api_token = (config and config.get("token")) or os.getenv("JENKINS_TOKEN")
        
        self.client = None
        self._initialized = False
        
        # Only initialize Jenkins client if we have the required URL
        if self.jenkins_url:
            try:
                self.client = JenkinsClient(
                    base_url=self.jenkins_url,
                    username=self.username,
                    token=self.api_token
                )
                self._initialized = True
            except Exception as e:
                print(f"Warning: Jenkins client initialization failed: {e}")
                self._initialized = False
        else:
            print("Warning: Jenkins URL not configured, client will not be initialized")
    
    @property
    def name(self) -> str:
        """Returns the unique name of the tool."""
        return "jenkins"
    
    @property
    def description(self) -> str:
        """Returns a description of what the tool does."""
        return "Jenkins integration tool for managing jobs, builds, and retrieving information"
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Jenkins operations based on input parameters.
        
        Args:
            input_data: Dictionary containing operation type and parameters
                - operation: str (get_job_info, get_build_info, get_all_jobs, etc.)
                - job_name: str (for job-specific operations)
                - build_number: int (for build-specific operations)
        
        Returns:
            dict: Operation results
        """
        operation = input_data.get('operation')
        
        try:
            if operation == 'get_job_info':
                job_name = input_data.get('job_name')
                return {'result': self.get_job_info(job_name)}
            elif operation == 'get_build_info':
                job_name = input_data.get('job_name')
                build_number = input_data.get('build_number')
                return {'result': self.get_build_info(job_name, build_number)}
            elif operation == 'get_build_logs':
                job_name = input_data.get('job_name')
                build_number = input_data.get('build_number')
                return {'result': self.get_build_logs(job_name, build_number)}
            elif operation == 'get_all_jobs':
                return {'result': self.get_all_jobs()}
            elif operation == 'trigger_build':
                job_name = input_data.get('job_name')
                params = input_data.get('params', {})
                return {'result': self.trigger_build(job_name, params)}
            elif operation == 'extract_complete_data':
                jenkins_url = input_data.get('jenkins_url')
                job_name = input_data.get('job_name')
                build_number = input_data.get('build_number')
                username = input_data.get('username')
                api_token = input_data.get('api_token')
                sanitize_logs = input_data.get('sanitize_logs', True)
                enable_advanced_pii = input_data.get('enable_advanced_pii', False)
                return {'result': self.extract_complete_data(
                    jenkins_url, job_name, build_number, username, api_token,
                    sanitize_logs, enable_advanced_pii
                )}
            elif operation == 'test_connection':
                return {'result': self.test_connection()}
            else:
                return {'error': f'Unknown operation: {operation}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get build information."""
        if not self._initialized:
            raise RuntimeError("Jenkins client not initialized. Check JENKINS_URL configuration.")
        return self.client.get_build(job_name, build_number)
    
    def get_build_logs(self, job_name: str, build_number: int) -> str:
        """Get build console logs."""
        if not self._initialized:
            raise RuntimeError("Jenkins client not initialized. Check JENKINS_URL configuration.")
        return self.client.get_build_logs(job_name, build_number)
    
    def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Get job information."""
        if not self._initialized:
            raise RuntimeError("Jenkins client not initialized. Check JENKINS_URL configuration.")
        return self.client.get_job_info(job_name)
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs."""
        if not self._initialized:
            raise RuntimeError("Jenkins client not initialized. Check JENKINS_URL configuration.")
        return self.client.get_jobs()
    
    def trigger_build(self, job_name: str, jenkins_url: Optional[str] = None, 
                     username: Optional[str] = None, api_token: Optional[str] = None,
                     params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Trigger a build. Can work with instance client or provided credentials.
        
        Args:
            job_name: Name of the job to trigger
            jenkins_url: Jenkins URL (optional, uses instance URL if not provided)
            username: Username (optional, uses instance username if not provided)
            api_token: API token (optional, uses instance token if not provided)
            params: Build parameters (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # If external credentials provided, use them directly
        if jenkins_url and username and api_token:
            try:
                temp_client = JenkinsClient(jenkins_url, username, api_token)
                temp_client.trigger_build(job_name, params)
                return True
            except Exception as e:
                print(f"Failed to trigger build with external credentials: {e}")
                return False
        
        # Use instance client
        if not self._initialized:
            raise RuntimeError("Jenkins client not initialized. Check JENKINS_URL configuration.")
        try:
            self.client.trigger_build(job_name, params)
            return True
        except Exception:
            return False
    
    def test_connection(self) -> bool:
        """Test Jenkins connection."""
        if not self._initialized:
            return False
        return self.client.test_connection()
    
    def get_status(self) -> Dict[str, Any]:
        """Get Jenkins tool status."""
        return {
            'jenkins_url': self.jenkins_url,
            'username': self.username,
            'connected': self.test_connection()
        }
    
    def extract_complete_data(self, jenkins_url: str, job_name: str, build_number: int, 
                             username: Optional[str] = None, api_token: Optional[str] = None,
                             sanitize_logs: bool = True, enable_advanced_pii: bool = False) -> Dict[str, Any]:
        """
        Extract complete Jenkins data including logs, Jenkinsfile, and metadata.
        
        Args:
            jenkins_url: Jenkins base URL
            job_name: Jenkins job name
            build_number: Build number
            username: Jenkins username (optional)
            api_token: Jenkins API token (optional)
            sanitize_logs: Enable sensitive data masking in logs (default: True)
            enable_advanced_pii: Enable advanced PII detection with Presidio (default: False)
        
        Returns:
            Dictionary with all extracted data
        """
        # Import the data extraction function
        from .jenkins.data_extractor import extract_complete_data
        
        # Use provided credentials or fall back to instance credentials
        final_username = username or self.username
        final_api_token = api_token or self.api_token
        final_jenkins_url = jenkins_url or self.jenkins_url
        
        if not final_jenkins_url:
            raise ValueError("Jenkins URL must be provided either in constructor or method call")
        
        return extract_complete_data(
            final_jenkins_url, 
            job_name, 
            build_number, 
            final_username, 
            final_api_token,
            sanitize_logs,
            enable_advanced_pii
        )
