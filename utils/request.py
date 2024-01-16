from dataclasses import dataclass, field

@dataclass
class Request:
    id: int = 0
    text: str = field(default="", repr=False)
