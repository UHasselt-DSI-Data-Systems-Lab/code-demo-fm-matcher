from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List, Tuple

from openai.types.completion_create_params import CompletionCreateParams


class Vote(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class Relation:
    name: str
    attributes: list = field(default_factory=list)
    description: str = None

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
    description: str = None

    def __hash__(self):
        return hash(self.name)

    @staticmethod
    def from_dict(json_obj: dict) -> Attribute:
        return Attribute(
            name=json_obj["name"],
            description=json_obj.get("description", None),
        )
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
        }


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


@dataclass
class Prompt:
    attributes: Tuple[List[Attribute], List[Attribute]]
    prompt: CompletionCreateParams


@dataclass
class Answer:
    attributes: Tuple[List[Attribute], List[Attribute]]
    answer: str
