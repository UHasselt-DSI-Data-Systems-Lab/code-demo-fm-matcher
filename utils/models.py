from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List


class Vote(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class Relation:
    name: str
    attributes: list = field(default_factory=list)
    description: str = None


@dataclass
class Attribute:
    name: str
    description: str = None

    def __hash__(self):
        return hash(self.name)


@dataclass
class AttributePair:
    source: Attribute
    target: Attribute

    def __hash__(self):
        return hash((self.source, self.target))


@dataclass
class Feedback:
    general: str
    per_attribute: Dict[Attribute, str] = field(default_factory=dict)
    per_attribute_pair: Dict[AttributePair, str] = field(default_factory=dict)


@dataclass
class Parameters:
    source_relation: Relation
    target_relation: Relation
    feedback: Feedback = None
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass
class Decision:
    vote: Vote
    explanation: str


@dataclass
class ResultPair:
    attributes: AttributePair
    votes: List[Decision] = field(default_factory=list)
    score: float = 0.0


@dataclass
class Result:
    name: str
    parameters: Parameters
    pairs: Dict[AttributePair, ResultPair] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)
