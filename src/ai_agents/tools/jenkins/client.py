"""Enhanced Jenkins API client wrapper with python-jenkins integration."""

import requests
from typing import Optional, Dict, Any
import jenkins


class JenkinsClient:
    """Enhanced Jenkins client that can work with both direct API calls and python-jenkins."""
    
    def __init__(self, base_url: str, username: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, token) if username and token else None
        
        # Also create a python-jenkins client for advanced operations
        self.jenkins_client = None
        try:
            if username and token:
                self.jenkins_client = jenkins.Jenkins(base_url, username=username, password=token)
            else:
                self.jenkins_client = jenkins.Jenkins(base_url)
        except Exception:
            # Fallback to direct API calls if python-jenkins fails
            pass

    def get_build(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get build information."""
        if self.jenkins_client:
            try:
                return self.jenkins_client.get_build_info(job_name, build_number)
            except Exception:
                pass
        
        # Fallback to direct API call
        url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def get_build_logs(self, job_name: str, build_number: int) -> str:
        """Get build console logs."""
        if self.jenkins_client:
            try:
                return self.jenkins_client.get_build_console_output(job_name, build_number)
            except Exception:
                pass
        
        # Fallback to direct API call
        url = f"{self.base_url}/job/{job_name}/{build_number}/consoleText"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.text

    def trigger_build(self, job_name: str, params: dict = None) -> int:
        """Trigger a new build."""
        if self.jenkins_client:
            try:
                if params:
                    return self.jenkins_client.build_job(job_name, params)
                else:
                    return self.jenkins_client.build_job(job_name)
            except Exception:
                pass
        
        # Fallback to direct API call
        url = f"{self.base_url}/job/{job_name}/build"
        r = requests.post(url, auth=self.auth, params=params)
        r.raise_for_status()
        return r.status_code

    def get_jobs(self) -> list:
        """Get list of all jobs."""
        if self.jenkins_client:
            try:
                return self.jenkins_client.get_jobs()
            except Exception:
                pass
        
        # Fallback to direct API call
        url = f"{self.base_url}/api/json"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        data = r.json()
        return data.get("jobs", [])

    def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Get detailed job information."""
        if self.jenkins_client:
            try:
                return self.jenkins_client.get_job_info(job_name)
            except Exception:
                pass
        
        # Fallback to direct API call
        url = f"{self.base_url}/job/{job_name}/api/json"
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def test_connection(self) -> bool:
        """Test Jenkins connection."""
        try:
            if self.jenkins_client:
                self.jenkins_client.get_whoami()
                return True
            else:
                # Test with direct API call
                url = f"{self.base_url}/api/json"
                r = requests.get(url, auth=self.auth, timeout=10)
                return r.status_code == 200
        except Exception:
            return False
