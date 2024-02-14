from dataclasses import dataclass, field
from enum import StrEnum
import json
from typing import Any, Dict, List, Optional

from openai.types.completion_create_params import CompletionCreateParams


class Vote(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class Attribute:
    name: str
    description: Optional[str] = None
    included: bool = field(default=True, compare=False)
    uid: Optional[int] = field(default=None, compare=False)

    def __hash__(self):
        return hash((self.name, self.description, self.included))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Attribute":
        return Attribute(**data)


@dataclass
class Relation:
    name: str
    attributes: List[Attribute] = field(default_factory=list)
    description: Optional[str] = None

    def __hash__(self):
        attrs = tuple(self.attributes)
        return hash((self.name, attrs, self.description))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Relation":
        return Relation(
            name=data["name"],
            attributes=[Attribute.from_dict(a) for a in data["attributes"]],
            description=data.get("description", None),
        )


@dataclass
class AttributePair:
    source: Attribute
    target: Attribute

    def __hash__(self):
        return hash((self.source, self.target))

    def __str__(self) -> str:
        return f"{self.source.name}->{self.target.name}"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AttributePair":
        return AttributePair(
            source=Attribute.from_dict(data["source"]),
            target=Attribute.from_dict(data["target"]),
        )


@dataclass
class Feedback:
    general: Optional[str] = None
    per_attribute: Dict[Attribute, str] = field(default_factory=dict)
    per_attribute_pair: Dict[AttributePair, str] = field(default_factory=dict)

    def __hash__(self):
        return hash(
            (
                self.general,
                tuple(self.per_attribute.keys()),
                tuple(self.per_attribute.values()),
                tuple(self.per_attribute_pair.keys()),
                tuple(self.per_attribute_pair.values()),
            )
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Feedback":
        return Feedback(
            general=data.get("general", None),
            per_attribute={
                Attribute.from_dict(k): v
                for k, v in data.get("per_attribute", {}).items()
            },
            per_attribute_pair={
                AttributePair.from_dict(k): v
                for k, v in data.get("per_attribute_pair", {}).items()
            },
        )


@dataclass
class Parameters:
    source_relation: Relation
    target_relation: Relation
    feedback: Feedback = Feedback()
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source_relation, self.target_relation, self.feedback))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Parameters":
        return Parameters(
            source_relation=Relation.from_dict(data["source_relation"]),
            target_relation=Relation.from_dict(data["target_relation"]),
            feedback=Feedback.from_dict(data.get("feedback", {})),
            meta=data.get("meta", {}),
        )


@dataclass
class Decision:
    vote: Vote
    explanation: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Decision":
        return Decision(
            vote=Vote(data["vote"]),
            explanation=data["explanation"],
        )


@dataclass
class ResultPair:
    attributes: AttributePair
    votes: List[Decision] = field(default_factory=list)
    score: float = 0.0

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ResultPair":
        return ResultPair(
            attributes=AttributePair.from_dict(data["attributes"]),
            votes=[Decision.from_dict(v) for v in data["votes"]],
            score=data.get("score", 0.0),
        )


@dataclass
class Result:
    parameters: Parameters
    name: Optional[str] = None
    pairs: Dict[AttributePair, ResultPair] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.parameters))

    def to_json(self) -> str:
        dct = {
            "parameters": self.parameters.asdict(),
            "name": self.name,
            "pairs": {
                str(k): {"key": k.asdict(), "value": v.asdict()}
                for k, v in self.pairs.items()
            },
            "meta": self.meta,
        }
        return json.dumps(dct)

    @staticmethod
    def from_json(jsn: str) -> Any:
        dct = json.loads(jsn)
        dct["pairs"] = {v["key"]: v["value"] for v in dct["pairs"].values()}
        return Result.from_dict(dct)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Result":
        return Result(
            parameters=Parameters.from_dict(data["parameters"]),
            name=data.get("name", None),
            pairs={
                AttributePair.from_dict(k): ResultPair.from_dict(v)
                for k, v in data["pairs"].items()
            },
            meta=data.get("meta", {}),
        )


@dataclass
class PromptAttributePair:
    sources: List[Attribute] = field(default_factory=list)
    targets: List[Attribute] = field(default_factory=list)

    def __hash__(self):
        return hash((tuple(self.sources), tuple(self.targets)))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PromptAttributePair":
        return PromptAttributePair(
            sources=[Attribute.from_dict(a) for a in data["sources"]],
            targets=[Attribute.from_dict(a) for a in data["targets"]],
        )


@dataclass
class Prompt:
    parameters: Parameters
    attributes: PromptAttributePair
    prompt: CompletionCreateParams
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.parameters, self.attributes))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Prompt":
        return Prompt(
            parameters=Parameters.from_dict(data["parameters"]),
            attributes=PromptAttributePair.from_dict(data["attributes"]),
            # CompetionCreateParams is a pydantic model, not a dataclass!
            prompt=CompletionCreateParams.parse_obj(data["prompt"]),
            meta=data.get("meta", {}),
        )


@dataclass
class Answer:
    attributes: PromptAttributePair
    answer: str
    valid: bool = False
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.attributes, self.answer))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Answer":
        return Answer(
            attributes=PromptAttributePair.from_dict(data["attributes"]),
            answer=data["answer"],
            valid=data.get("valid", False),
            meta=data.get("meta", {}),
        )
