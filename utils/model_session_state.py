"""A dataclass to store all session data in the Streamlit app."""

from dataclasses import dataclass, field
from typing import Optional
from utils.models import Relation, Result

@dataclass
class ModelSessionState:
    """A dataclass to store all session data in the Streamlit app."""
    source_relation: Optional[Relation] = None
    target_relation: Optional[Relation] = None
    input_fixed: bool = False
    result: Optional[Result] = None

