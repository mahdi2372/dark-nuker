"""Template rendering for generated names."""

from __future__ import annotations

import random
import string
from typing import Any


def render_template(template: str, index: int, context: dict[str, Any] | None = None) -> str:
    context = context or {}
    result = template
    result = result.replace("{i}", str(index))
    result = result.replace("{index}", str(index))
    result = result.replace("{random}", "".join(random.choices(string.ascii_lowercase + string.digits, k=6)))
    for key, value in context.items():
        result = result.replace("{" + key + "}", str(value))
    return result[:100]


def random_name(prefix: str = "nuke", length: int = 6) -> str:
    return f"{prefix}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=length))}"
