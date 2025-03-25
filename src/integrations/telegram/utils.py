"""Utilities for Telegram bot integration."""

from typing import Dict, Any, List, Optional
from telegram import Update
from loguru import logger

async def send_typing_action(update: Update):
    """
    Send typing action to indicate the bot is processing a message.
    
    Args:
        update: The Telegram update object
    """
    try:
        await update.message.chat.send_action(action="typing")
    except Exception as e:
        logger.error(f"Error sending typing action: {e}")

def format_work_summary(entries: List[Dict[str, Any]]) -> str:
    """
    Format a list of work entries as a readable summary.
    
    Args:
        entries: List of work entry dictionaries
        
    Returns:
        Formatted summary text
    """
    if not entries:
        return "No work entries found."
    
    # Calculate total hours
    total_hours = sum(float(entry.get("Hours", 0)) for entry in entries)
    billable_hours = sum(float(entry.get("Hours", 0)) 
                         for entry in entries if entry.get("Billable") == "Yes")
    
    # Group by client and project
    client_projects = {}
    for entry in entries:
        client = entry.get("Client", "Unspecified")
        project = entry.get("Project", "Unspecified")
        hours = float(entry.get("Hours", 0))
        
        if client not in client_projects:
            client_projects[client] = {}
        
        if project not in client_projects[client]:
            client_projects[client][project] = 0
            
        client_projects[client][project] += hours
    
    # Format the summary
    summary = f"📊 *Work Summary*\n\n"
    summary += f"Total Hours: {total_hours:.1f}\n"
    summary += f"Billable Hours: {billable_hours:.1f}\n\n"
    
    for client, projects in client_projects.items():
        client_total = sum(projects.values())
        summary += f"*{client}*: {client_total:.1f} hours\n"
        
        for project, hours in projects.items():
            summary += f"  - {project}: {hours:.1f} hours\n"
        
        summary += "\n"
    
    return summary