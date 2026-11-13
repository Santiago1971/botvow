"""botvow_translate — translate agent messages between MCP, A2A (0.3 and 1.0) and plain email.

Pure functions, standard library only. It NEVER executes a request and NEVER opens a network
connection: it only rewrites the message into another format and reports what was lost or guessed.
"""
from .core import Envelope, detect, parse, render, translate, TranslationError, MAX_BYTES

__all__ = ["Envelope", "detect", "parse", "render", "translate", "TranslationError", "MAX_BYTES"]
__version__ = "0.1.0"
