"""A dataclass to store all session data in the Streamlit app."""

from dataclasses import dataclass, field
from typing import List, Optional
from utils.models import AttributePair, Feedback, Relation, Result

@dataclass
class ModelSessionState:
    """A dataclass to store all session data in the Streamlit app."""
    source_relation: Optional[Relation] = None
    target_relation: Optional[Relation] = None
    input_fixed: bool = False
    result: Optional[Result] = None
    compare_to: Optional[Result] = None
    all_results: list[Result] = field(default_factory=list)
    feedback: Optional[Feedback] = None
    uid_counter: int = 0 # used for generating unique ids for attributes
    experiment_counter: int = 0 # used for generating unique ids for experiments
    selected_attrs: list[int] = field(default_factory=list)
    selected_llm: str = None  # llm selected by the user (will be persisted in the parameters
    ground_truth: List[AttributePair] = field(default_factory=list)  # a list of attribute pairs that represent the ground truth
    ground_truth_enabled: bool = False

    def get_next_uid(self) -> int:
        """Returns the next unique id."""
        self.uid_counter += 1
        return self.uid_counter
    
    def get_next_experiment_id(self) -> int:
        """Returns the next unique id."""
        self.experiment_counter += 1
        return self.experiment_counter

