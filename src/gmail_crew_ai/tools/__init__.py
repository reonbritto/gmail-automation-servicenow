# This file makes the tools directory a proper Python package

from .gmail_tools import (
    GetUnreadEmailsTool, 
    SaveDraftTool, 
    GmailOrganizeTool, 
    GmailDeleteTool,
    EmptyTrashTool,
    GetThreadHistoryTool,  # Add new tool
    ContextAwareReplyTool,  # Add new tool
)

__all__ = [
    "GetUnreadEmailsTool",
    "SaveDraftTool",
    "GmailOrganizeTool",
    "GmailDeleteTool",
    "EmptyTrashTool",
    "GetThreadHistoryTool",  # Add new tool
    "ContextAwareReplyTool",  # Add new tool
]
