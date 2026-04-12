"""
MkDocs hooks to register custom Pygments lexers for Lime docs.
"""

import os
import sys


def _register_lime_lexer():
    # Ensure docs/ is on the import path so local lexers resolve reliably.
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    if docs_dir not in sys.path:
        sys.path.insert(0, docs_dir)

    from lexers.lime_lexer import LimeLexer
    from pygments.lexers import _mapping

    if "LimeLexer" not in _mapping.LEXERS:
        _mapping.LEXERS["LimeLexer"] = (
            LimeLexer.__module__,
            "Lime",
            ("lime", "mgx", "margarita", "marg", "mg", "margaritascript"),
            ("*.mgx", "*.mg", "*.margarita"),
            ("text/x-lime", "text/x-margarita"),
        )
        print("✓ Registered Lime syntax highlighter")


def on_startup(**kwargs):
    """Register custom Pygments lexers when MkDocs starts."""
    try:
        _register_lime_lexer()
    except Exception as e:
        print(f"Warning: Could not register Lime lexer: {e}")


def on_config(config, **kwargs):
    """Register lexers before MkDocs config is finalised."""
    try:
        _register_lime_lexer()
    except Exception as e:
        print(f"Warning: Could not register Lime lexer: {e}")
    return config
