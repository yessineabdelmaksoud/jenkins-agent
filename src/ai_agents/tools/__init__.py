"""Initialize the tools package."""

from .base import BaseTool
from .tool_registry import ToolRegistry
from .jenkins_wrapper import JenkinsWrapper
from .notifications_wrapper import NotificationsWrapper

# Auto-register tools
ToolRegistry.register(JenkinsWrapper)
ToolRegistry.register(NotificationsWrapper)

__all__ = ['BaseTool', 'ToolRegistry', 'JenkinsWrapper', 'NotificationsWrapper']
