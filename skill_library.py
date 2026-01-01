from __future__ import annotations

# Bridge module: keep tool auto-discovery working (askq.mcp.autodiscover_tools imports *.py here).
# Actual implementation lives in `askq.mcp.skill_library`.

from askq.mcp.skill_library import (  # noqa: F401
    list_available_skills,
    load_skill_instructions,
    wrap_python_function_as_tool,
)

__all__ = [
    "list_available_skills",
    "load_skill_instructions",
    "wrap_python_function_as_tool",
]
