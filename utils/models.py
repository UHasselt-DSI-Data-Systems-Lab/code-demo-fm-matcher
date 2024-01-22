from dataclasses import dataclass, field, fields
from enum import StrEnum
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


@dataclass
class Attribute:
    name: str
    description: Optional[str] = None
    included: bool = True

    def __hash__(self):
        return hash((self.name, self.description))


@dataclass
class Relation:
    name: str
    attributes: List[Attribute] = field(default_factory=list)
    description: Optional[str] = None


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
