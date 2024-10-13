from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any, Dict, List, Optional

from openai.types.completion_create_params import CompletionCreateParams


class Vote(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class Side(StrEnum):
    SOURCE = "source"
    TARGET = "target"


@dataclass(order=True)
class Attribute:
    name: str
    description: Optional[str] = None
    included: bool = field(default=True, compare=False)

    def digest(self) -> str:
        return hashlib.blake2s(
            (self.name + str(self.description) + str(self.included)).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Attribute":
        return Attribute(**data)


@dataclass
class Relation:
    name: str
    side: Side
    attributes: List[Attribute] = field(default_factory=list)
    description: Optional[str] = None

    def digest(self) -> str:
        return hashlib.blake2s(
            (
                self.name
                + self.side.value
                + "".join([a.digest() for a in sorted(self.attributes)])
                + str(self.description)
            ).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Relation":
        return Relation(
            name=data["name"],
            side=Side(data["side"]),
            attributes=[Attribute.from_dict(a) for a in data["attributes"]],
            description=data.get("description", None),
        )


@dataclass(order=True)
class AttributePair:
    source: Attribute
    target: Attribute

    def digest(self) -> str:
        return hashlib.blake2s(
            (self.source.digest() + self.target.digest()).encode()
        ).hexdigest()

    def __str__(self) -> str:
        return f"{self.source.name}->{self.target.name}"

    def __hash__(self) -> int:
        return hash(self.digest())

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

    def digest(self) -> str:
        return hashlib.blake2s(
            (
                str(self.general)
                + "".join(
                    [
                        a.digest() + self.per_attribute[a]
                        for a in sorted(self.per_attribute)
                    ]
                )
                + "".join(
                    [
                        ap.digest() + self.per_attribute_pair[ap]
                        for ap in sorted(self.per_attribute_pair)
                    ]
                )
            ).encode()
        ).hexdigest()

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
    feedback: Feedback = field(default_factory=Feedback)
    meta: Dict[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        return hashlib.blake2s(
            (
                self.source_relation.digest()
                + self.target_relation.digest()
                + self.feedback.digest()
            ).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Parameters":
        return Parameters(
            source_relation=Relation.from_dict(data["source_relation"]),
            target_relation=Relation.from_dict(data["target_relation"]),
            feedback=Feedback.from_dict(data.get("feedback", {})),
            meta=data.get("meta", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PromptAttributePair:
    sources: List[Attribute] = field(default_factory=list)
    targets: List[Attribute] = field(default_factory=list)

    def digest(self) -> str:
        return hashlib.blake2b(
            (
                "".join([a.digest() for a in sorted(self.sources)])
                + "".join([a.digest() for a in sorted(self.targets)])
            ).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PromptAttributePair":
        return PromptAttributePair(
            sources=[Attribute.from_dict(a) for a in data["sources"]],
            targets=[Attribute.from_dict(a) for a in data["targets"]],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Prompt:
    parameters: Parameters
    attributes: PromptAttributePair
    prompt: CompletionCreateParams
    meta: Dict[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        prompt_digest = hashlib.blake2s(
            (
                self.prompt.get("model", "")
                + str(self.prompt.get("temperature", 1))
                + "".join([m["role"] + m["content"] for m in self.prompt["messages"]])
                + str(self.prompt.get("n", 1))
                + str(self.prompt.get("timeout", 60))
            ).encode()
        ).hexdigest()

        return hashlib.blake2s(
            (
                self.parameters.digest() + self.attributes.digest() + prompt_digest
            ).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Prompt":
        return Prompt(
            parameters=Parameters.from_dict(data["parameters"]),
            attributes=PromptAttributePair.from_dict(data["attributes"]),
            # CompetionCreateParams is a pydantic model, not a dataclass!
            prompt=data["prompt"],
            meta=data.get("meta", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Answer:
    attributes: PromptAttributePair
    answer: str
    index: int = 0
    valid: bool = False
    meta: Dict[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        return hashlib.blake2s(
            (
                self.attributes.digest()
                + str(self.index)
                + self.answer
                + str(self.valid)
            ).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Answer":
        return Answer(
            attributes=PromptAttributePair.from_dict(data["attributes"]),
            answer=data["answer"],
            index=data["index"],
            valid=data.get("valid", False),
            meta=data.get("meta", {}),
        )

    def __lt__(self, other: "Answer") -> bool:
        return self.index < other.index

    def __le__(self, other: "Answer") -> bool:
        return self.index <= other.index

    def __gt__(self, other: "Answer") -> bool:
        return self.index > other.index

    def __ge__(self, other: "Answer") -> bool:
        return self.index >= other.index

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(order=True)
class Decision:
    vote: Vote
    explanation: str
    answer: Optional[Answer] = None

    def digest(self) -> str:
        return hashlib.blake2s(
            (self.vote.value + self.explanation).encode()
        ).hexdigest()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Decision":
        answer = data.get("answer", {})
        if answer:
            answer = Answer.from_dict(answer)
        return Decision(
            vote=Vote(data["vote"]),
            explanation=data["explanation"],
            answer=answer,
        )


@dataclass
class ResultPair:
    attributes: AttributePair
    votes: List[Decision] = field(default_factory=list)
    score: float = 0.0

    def digest(self) -> str:
        return hashlib.blake2s(
            (
                self.attributes.digest()
                + "".join([d.digest() for d in sorted(self.votes)])
                + str(self.score)
            ).encode()
        ).hexdigest()

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

    def digest(self) -> str:
        return hashlib.blake2s(
            (
                self.parameters.digest()
                + "".join(
                    [p.digest() + self.pairs[p].digest() for p in sorted(self.pairs)]
                )
            ).encode()
        ).hexdigest()

    def to_json(self) -> str:
        dct = {
            "parameters": self.parameters.to_dict(),
            "name": self.name,
            "pairs": {
                str(k): {"key": asdict(k), "value": asdict(v)}
                for k, v in self.pairs.items()
            },
            "meta": self.meta,
        }
        return json.dumps(dct)

    @staticmethod
    def from_json(jsn: str) -> Any:
        dct = json.loads(jsn)
        return Result.from_dict(dct)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Result":
        return Result(
            parameters=Parameters.from_dict(data["parameters"]),
            name=data.get("name", None),
            pairs={
                AttributePair.from_dict(v["key"]): ResultPair.from_dict(v["value"])
                for v in data["pairs"].values()
            },
            meta=data.get("meta", {}),
        )
