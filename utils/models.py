from dataclasses import asdict, dataclass, field, fields
from enum import StrEnum
import json
from typing import Any, Dict, List, Optional, get_args, get_origin

from openai.types.completion_create_params import CompletionCreateParams


def generic_from_dict(cls: dataclass, data: Any) -> Any:
    """Conerts a dictionary to a dataclass object given in cls.
    Thanks to Salman Mehmood of https://www.delftstack.com/howto/python/python-dataclass-from-dict/
    I added the possibility to convert lists of dataclasses as well. When using this method, make sure that all attributes are properly annotated with their types, e.g. `List[Attributes]` instead of `list`.
    """
    if get_origin(cls) == list:
        return [generic_from_dict(get_args(cls)[0], d) for d in data]
    try:
        types = {f.name: f.type for f in fields(cls)}
        return cls(**{f: generic_from_dict(types[f], data[f]) for f in data})
    except:  # noqa: E722
        return data


class Vote(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class Dictable:
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        return generic_from_dict(cls, data)


@dataclass
class Attribute:
    name: str
    description: Optional[str] = None
    included: bool = True

    def __hash__(self):
        return hash((self.name, self.description, self.included))


@dataclass
class Relation:
    name: str
    attributes: List[Attribute] = field(default_factory=list)
    description: Optional[str] = None

    def __hash__(self):
        attrs = tuple(self.attributes)
        return hash((self.name, attrs, self.description))


@dataclass
class AttributePair(Dictable):
    source: Attribute
    target: Attribute

    def __hash__(self):
        return hash((self.source, self.target))

    def __str__(self) -> str:
        return f"{self.source.name}->{self.target.name}"


@dataclass
class Feedback:
    general: Optional[str]
    per_attribute: Dict[Attribute, str] = field(default_factory=dict)
    per_attribute_pair: Dict[AttributePair, str] = field(default_factory=dict)


@dataclass
class Parameters(Dictable):
    source_relation: Relation
    target_relation: Relation
    feedback: Feedback = None
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source_relation, self.target_relation))


@dataclass
class Decision:
    vote: Vote
    explanation: str


@dataclass
class ResultPair(Dictable):
    attributes: AttributePair
    votes: List[Decision] = field(default_factory=list)
    score: float = 0.0


@dataclass
class Result(Dictable):
    parameters: Parameters
    name: Optional[str] = None
    pairs: Dict[AttributePair, ResultPair] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.parameters))

    def to_json(self) -> str:
        dct = {
            "parameters": self.parameters.to_dict(),
            "name": self.name,
            "pairs": {
                str(k): {"key": k.to_dict(), "value": v.to_dict()}
                for k, v in self.pairs.items()
            },
            "meta": self.meta,
        }
        return json.dumps(dct)

    def from_json(jsn: str) -> Any:
        dct = json.loads(jsn)
        return Result(
            parameters=Parameters.from_dict(dct["parameters"]),
            name=dct["name"] if "name" in dct else None,
            pairs={
                AttributePair.from_dict(v["key"]): ResultPair.from_dict(v["value"])
                for v in dct["pairs"].values()
            },
            meta=dct["meta"],
        )


@dataclass
class PromptAttributePair:
    sources: List[Attribute] = field(default_factory=list)
    targets: List[Attribute] = field(default_factory=list)

    def __hash__(self):
        return hash((tuple(self.sources), tuple(self.targets)))


@dataclass
class Prompt(Dictable):
    parameters: Parameters
    attributes: PromptAttributePair
    prompt: CompletionCreateParams
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.parameters, self.attributes))


@dataclass
class Answer(Dictable):
    attributes: PromptAttributePair
    answer: str
    valid: bool = False
    meta: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.attributes, self.answer))
