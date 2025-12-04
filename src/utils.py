"""
Utility functions for the application.
"""

def format_bytes(size):
    """
    Formats a size in bytes to a human-readable string (B, KB, MB, GB).
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"