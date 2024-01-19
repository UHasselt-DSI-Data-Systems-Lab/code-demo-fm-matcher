from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List, Optional

from openai.types.completion_create_params import CompletionCreateParams


class Vote(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class Relation:
    name: str
    attributes: list = field(default_factory=list)
    description: Optional[str] = None

    @staticmethod
    def from_dict(json_obj: dict) -> Relation:
        return Relation(
            name=json_obj["name"],
            attributes=[
                Attribute.from_dict(attr) for attr in json_obj["attributes"]
            ],
            description=json_obj.get("description", ""),
        )
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "attributes": [attr.to_dict() for attr in self.attributes],
            "description": self.description,
        }


@dataclass
class Attribute:
    name: str
    description: Optional[str] = None
    included: bool = True

    def __hash__(self):
        return hash(self.name)

    @staticmethod
    def from_dict(json_obj: dict) -> Attribute:
        return Attribute(
            name=json_obj["name"],
            description=json_obj.get("description", None),
            included=json_obj.get("included", True),
        )
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "included": self.included,
        }


@dataclass
class AttributePair:
    source: Attribute
    target: Attribute

    def __hash__(self):
        return hash((self.source, self.target))


@dataclass
class Feedback:
    general: Optional[str]
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


@dataclass
class PromptAttributePair:
    sources: List[Attribute] = field(default_factory=list)
    targets: List[Attribute] = field(default_factory=list)


@dataclass
class Prompt:
    attributes: PromptAttributePair
    prompt: CompletionCreateParams


@dataclass
class Answer:
    attributes: PromptAttributePair
    answer: str