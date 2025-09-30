"""
Revit Warnings Manager package.

This package provides tools for parsing Revit warning files, journal files,
and managing UI for warnings analysis.
"""

from app import RevitManager
from ui import UIManager
from handlers import EventHandlers
from file_operations import FileOperations
from parsers import (
    ErrorHandler,
    HTMLParser,
    JournalParser,
    WorkerLogParser,
    JournalProblemFinder
)

__all__ = [
    'RevitManager',
    'UIManager',
    'EventHandlers',
    'FileOperations',
    'ErrorHandler',
    'HTMLParser',
    'JournalParser',
    'WorkerLogParser',
    'JournalProblemFinder'
]

__version__ = "1.0.0"
