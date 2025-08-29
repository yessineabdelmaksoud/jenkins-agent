"""Jenkins polling service for monitoring builds."""

import asyncio
import logging
import time
import requests
from typing import Dict, Set, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
import os

from ai_agents.tools import ToolRegistry
from ai_agents.deployment.api_agent.core.logging import get_logger
from ai_agents.deployment.api_agent.services.agent_service import AgentService


@dataclass
class BuildInfo:
    """Build information data class."""
    job_name: str
    build_number: int
    result: Optional[str]
    building: bool
    timestamp: int
    url: str


class JenkinsPollingService:
    """Service for polling Jenkins builds and sending webhook requests."""
    
    def __init__(self, poll_interval: int = 5):
        """
        Initialize the Jenkins polling service.
        
        Args:
            poll_interval: Polling interval in seconds (default: 5)
        """
        self.logger = get_logger(__name__)
        self.poll_interval = poll_interval
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Jenkins connection
        self.jenkins_url = os.getenv("JENKINS_URL")
        self.jenkins_user = os.getenv("JENKINS_USER")
        self.jenkins_token = os.getenv("JENKINS_TOKEN")
        
        # Use JenkinsWrapper instead of direct jenkins client
        self.jenkins_tool = None
        self.known_last_builds: Dict[str, int] = {}
        self.monitored_builds: Set[str] = set()  # Set of "job_name#build_number"
        
        # Control flags
        self._polling = False
        self._stop_event = asyncio.Event()
        
        self.logger.info(f"Jenkins polling service initialized with interval: {poll_interval}s")
    
    def _create_jenkins_client(self):
        """Create Jenkins client connection using JenkinsWrapper."""
        try:
            if not self.jenkins_url:
                self.logger.error("JENKINS_URL not configured")
                return None
            
            # Get Jenkins tool from registry
            jenkins_tool_class = ToolRegistry.get_tool("jenkins")
            config = {
                "jenkins_url": self.jenkins_url,
                "username": self.jenkins_user,
                "token": self.jenkins_token
            }
            
            jenkins_tool = jenkins_tool_class(config)
            
            # Test connection
            if jenkins_tool.test_connection():
                self.logger.info(f"Successfully connected to Jenkins at {self.jenkins_url}")
                return jenkins_tool
            else:
                self.logger.error("Failed to connect to Jenkins - connection test failed")
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Jenkins: {e}")
            return None
    
    def _monitor_build(self, job_name: str, build_number: int) -> Optional[str]:
        """
        Monitor a specific build until completion.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number to monitor
            
        Returns:
            Build result when completed, None if error
        """
        build_key = f"{job_name}#{build_number}"
        self.logger.info(f"Start monitoring {build_key}")
        
        try:
            while True:
                if self._stop_event.is_set():
                    break
                    
                # Use JenkinsWrapper to get build info
                if not self.jenkins_tool:
                    self.logger.error("Jenkins tool not available")
                    break
                
                info = self.jenkins_tool.get_build_info(job_name, build_number)
                building = info.get("building", False)
                result = info.get("result")
                
                self.logger.debug(f"{build_key} building={building} result={result}")
                
                if not building:
                    self.logger.info(f"Build finished: {build_key} -> {result}")
                    self.monitored_builds.discard(build_key)
                    
                    # Send webhook request instead of directly triggering agent
                    self._send_webhook_request(job_name, build_number, info)
                    return result
                
                time.sleep(2)  # Check every 2 seconds
                
        except Exception as e:
            if "not found" in str(e).lower():
                self.logger.warning(f"{build_key} not found (may be ephemeral)")
            else:
                self.logger.exception(f"Error monitoring {build_key}: {e}")
            self.monitored_builds.discard(build_key)
        
        return None
    
    def _send_webhook_request(self, job_name: str, build_number: int, build_info: Dict[str, Any]):
        """
        Send a webhook request to trigger the Jenkins agent (instead of directly calling it).
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            build_info: Full build information from Jenkins API
        """
        try:
            import requests
            
            # Create webhook-like payload similar to what Jenkins would send
            webhook_payload = {
                "name": job_name,
                "job_name": job_name,
                "build_number": build_number,
                "jenkins_url": self.jenkins_url,
                "build": {
                    "number": build_number,
                    "phase": "COMPLETED",  # Mark as completed for processing
                    "status": build_info.get("result", "UNKNOWN").upper(),
                    "url": build_info.get("url", ""),
                    "full_url": build_info.get("url", ""),
                    "timestamp": build_info.get("timestamp", int(time.time() * 1000)),
                    "duration": build_info.get("duration", 0)
                },
                "triggered_by": "jenkins_polling_service",
                "polling_timestamp": datetime.now().isoformat()
            }
            
            # Get API base URL from environment or use localhost
            api_host = os.getenv("HOST", "localhost")
            api_port = os.getenv("PORT", "8000")
            webhook_url = f"http://{api_host}:{api_port}/api/jenkins/webhook"
            
            self.logger.info(f"Sending webhook request for {job_name}#{build_number} to {webhook_url}")
            
            # Send POST request to webhook endpoint
            response = requests.post(
                webhook_url,
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully sent webhook for {job_name}#{build_number}")
            else:
                self.logger.error(f"Webhook request failed for {job_name}#{build_number}: {response.status_code} - {response.text}")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook request for {job_name}#{build_number}: {e}")
    
    def _polling_loop(self):
        """Main polling loop that runs in a separate thread."""
        self.logger.info("Starting Jenkins polling loop (monitoring for new builds)")
        
        while self._polling and not self._stop_event.is_set():
            try:
                if not self.jenkins_tool:
                    self.jenkins_tool = self._create_jenkins_client()
                    if not self.jenkins_tool:
                        self.logger.error("Cannot connect to Jenkins, retrying in 30 seconds")
                        time.sleep(30)
                        continue
                
                # Get all jobs using JenkinsWrapper
                jobs = self.jenkins_tool.get_all_jobs()
                
                for job in jobs:
                    if self._stop_event.is_set():
                        break
                        
                    job_name = job.get("name")
                    if not job_name:
                        continue
                    
                    try:
                        # Get job info to check for new builds using JenkinsWrapper
                        job_info = self.jenkins_tool.get_job_info(job_name)
                        last_build = job_info.get("lastBuild")
                        
                        if last_build:
                            current_build_number = last_build.get("number")
                            previous_build_number = self.known_last_builds.get(job_name)
                            
                            if previous_build_number is None:
                                # First time seeing this job, just record the current build
                                self.known_last_builds[job_name] = current_build_number
                                self.logger.debug(f"Initialized tracking for {job_name} at build #{current_build_number}")
                            elif current_build_number > previous_build_number:
                                # New build detected!
                                self.logger.info(f"🆕 New build detected: {job_name} #{current_build_number}")
                                self.known_last_builds[job_name] = current_build_number
                                
                                # Start monitoring this build in background
                                build_key = f"{job_name}#{current_build_number}"
                                if build_key not in self.monitored_builds:
                                    self.monitored_builds.add(build_key)
                                    self.executor.submit(
                                        self._monitor_build, 
                                        job_name, 
                                        current_build_number
                                    )
                    
                    except Exception as e:
                        self.logger.debug(f"Could not fetch job info for {job_name}: {e}")
                
                # Sleep before next poll cycle
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Polling loop interrupted by user")
                break
            except Exception as e:
                self.logger.exception(f"Polling loop error: {e}")
                time.sleep(self.poll_interval)
        
        self.logger.info("Jenkins polling loop stopped")
    
    async def start_polling(self):
        """Start the Jenkins polling service."""
        if self._polling:
            self.logger.warning("Polling service is already running")
            return
        
        self.logger.info("Starting Jenkins polling service...")
        
        # Validate configuration
        if not self.jenkins_url:
            raise ValueError("JENKINS_URL environment variable is required")
        
        self._polling = True
        self._stop_event.clear()
        
        # Start polling in a separate thread (non-blocking)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._polling_loop)
    
    async def stop_polling(self):
        """Stop the Jenkins polling service."""
        if not self._polling:
            self.logger.warning("Polling service is not running")
            return
        
        self.logger.info("Stopping Jenkins polling service...")
        self._polling = False
        self._stop_event.set()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Jenkins polling service stopped")
    
    def is_polling(self) -> bool:
        """Check if the polling service is currently running."""
        return self._polling
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the polling service."""
        return {
            "is_polling": self._polling,
            "jenkins_url": self.jenkins_url,
            "jenkins_user": self.jenkins_user,
            "jenkins_connected": self.jenkins_tool is not None,
            "poll_interval": self.poll_interval,
            "known_jobs": len(self.known_last_builds),
            "monitored_builds": len(self.monitored_builds),
            "known_last_builds": self.known_last_builds.copy(),
            "current_monitored_builds": list(self.monitored_builds)
        }
