"""Wrapper for notification tools to integrate with tool registry."""

import os
from typing import Dict, Any, Optional, List
from .base import BaseTool
from .notifications.email_notifier import notify_email
from .notifications.slack_notifier import notify_slack


class NotificationsWrapper(BaseTool):
    """Wrapper for notification tools that integrates with tool registry."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    @property
    def name(self) -> str:
        """Returns the unique name of the tool."""
        return "notifications"
    
    @property
    def description(self) -> str:
        """Returns a description of what the tool does."""
        return "Multi-channel notification tool supporting email and Slack notifications"
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute notification operations based on input parameters.
        
        Args:
            input_data: Dictionary containing operation type and parameters
                - operation: str (send_email, send_slack, send_jenkins_notification, get_status)
                - subject: str (for email)
                - message: str (for notifications)
                - recipients: List[str] (for email)
                - job: str (for Jenkins notifications)
                - build: int (for Jenkins notifications)
                - status: str (for Jenkins notifications)
                - summary: Any (for Jenkins notifications)
        
        Returns:
            dict: Operation results
        """
        operation = input_data.get('operation')
        
        try:
            if operation == 'send_email':
                subject = input_data.get('subject', 'Notification')
                message = input_data.get('message', '')
                recipients = input_data.get('recipients')
                return {'result': self.send_email(subject, message, recipients)}
            elif operation == 'send_slack':
                message = input_data.get('message', '')
                return {'result': self.send_slack(message)}
            elif operation == 'send_jenkins_notification':
                job = input_data.get('job')
                build = input_data.get('build')
                status = input_data.get('status')
                summary = input_data.get('summary')
                action = input_data.get('action', 'notified')
                return {'result': self.send_jenkins_notification(job, build, status, summary, action)}
            elif operation == 'send_all_notifications':
                subject = input_data.get('subject', 'Notification')
                message = input_data.get('message', '')
                kwargs = input_data.get('kwargs', {})
                return {'result': self.send_all_notifications(subject, message, **kwargs)}
            elif operation == 'get_status':
                return {'result': self.get_status()}
            else:
                return {'error': f'Unknown operation: {operation}'}
        except Exception as e:
            return {'error': str(e)}
    
    def send_email(self, email_cfg_or_subject, content_or_body=None, recipients: List[str] = None) -> bool:
        """
        Send email notification. Supports two calling patterns:
        1. Legacy: send_email(email_cfg_dict, content_dict) - for handlers
        2. New: send_email(subject_str, body_str, recipients_list) - for direct use
        """
        try:
            # Pattern 1: Handler style - send_email(config_dict, content_dict)
            if isinstance(email_cfg_or_subject, dict) and isinstance(content_or_body, dict):
                config = email_cfg_or_subject
                content = content_or_body
                notify_email(config, content)
                return True
            
            # Pattern 2: Direct style - send_email(subject, body, recipients)
            else:
                subject = email_cfg_or_subject
                body = content_or_body or ''
                # Prepare config dict for notify_email function
                config = {
                    'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                    'username': os.getenv('EMAIL_SENDER'),
                    'password': os.getenv('EMAIL_PASSWORD'),
                    'to': recipients or os.getenv('EMAIL_TO', '').split(','),
                    'subject': subject,
                    'body': body
                }
                
                # Prepare content dict
                content = {
                    'summary': body
                }
                
                notify_email(config, content)
                return True
                
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

    def send_slack(self, webhook_url_or_message, content_or_channel=None) -> bool:
        """
        Send Slack notification. Supports two calling patterns:
        1. Legacy: send_slack(webhook_url, content_dict) - for handlers  
        2. New: send_slack(message_str, channel_str) - for direct use
        """
        try:
            # Pattern 1: Handler style - send_slack(webhook_url, content_dict)
            if isinstance(content_or_channel, dict):
                webhook_url = webhook_url_or_message
                content = content_or_channel
                notify_slack(webhook_url, content)
                return True
            
            # Pattern 2: Direct style - send_slack(message, channel)
            else:
                message = webhook_url_or_message
                webhook_url = os.getenv('SLACK_WEBHOOK_URL')
                if not webhook_url:
                    print("Slack webhook URL not configured")
                    return False
                    
                # Prepare content dict for notify_slack function
                content = {
                    'job': 'notification',
                    'build': 0,
                    'status': 'INFO',
                    'action': 'sent',
                    'summary': message
                }
                
                notify_slack(webhook_url, content)
                return True
                
        except Exception as e:
            print(f"Slack sending failed: {e}")
            return False
    
    def send_jenkins_notification(self, job: str, build: int, status: str, summary: Any, action: str = 'notified') -> Dict[str, bool]:
        """Send Jenkins-specific notifications via all configured channels."""
        results = {}
        
        # Prepare content dict for Jenkins notification
        content = {
            'job': job,
            'build': build,
            'status': status,
            'action': action,
            'summary': summary
        }
        
        # Send email if configured
        if self.get_email_status()['configured']:
            try:
                config = {
                    'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                    'username': os.getenv('EMAIL_SENDER'),
                    'password': os.getenv('EMAIL_PASSWORD'),
                    'to': os.getenv('EMAIL_TO', '').split(',')
                }
                notify_email(config, content)
                results['email'] = True
            except Exception as e:
                print(f"Email notification failed: {e}")
                results['email'] = False
        else:
            results['email'] = False
            
        # Send Slack if configured
        if self.get_slack_status()['configured']:
            try:
                webhook_url = os.getenv('SLACK_WEBHOOK_URL')
                notify_slack(webhook_url, content)
                results['slack'] = True
            except Exception as e:
                print(f"Slack notification failed: {e}")
                results['slack'] = False
        else:
            results['slack'] = False
            
        return results
    
    def send_all_notifications(self, subject: str, message: str, **kwargs) -> Dict[str, bool]:
        """Send notifications via all configured channels."""
        results = {}
        
        # Send email
        email_recipients = kwargs.get('email_recipients')
        email_result = self.send_email(subject, message, email_recipients)
        results['email'] = email_result
        
        # Send Slack
        slack_result = self.send_slack(message)
        results['slack'] = slack_result
        
        return results
    
    def get_email_status(self) -> Dict[str, Any]:
        """Get email configuration status."""
        return {
            'configured': bool(os.getenv('EMAIL_SENDER') and os.getenv('EMAIL_PASSWORD')),
            'sender': os.getenv('EMAIL_SENDER', 'Not configured')
        }
    
    def get_slack_status(self) -> Dict[str, Any]:
        """Get Slack configuration status."""
        return {
            'configured': bool(os.getenv('SLACK_WEBHOOK_URL')),
            'webhook_url': '✅ Configured' if os.getenv('SLACK_WEBHOOK_URL') else '❌ Not configured'
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get notification tools status."""
        return {
            'email': self.get_email_status(),
            'slack': self.get_slack_status()
        }
