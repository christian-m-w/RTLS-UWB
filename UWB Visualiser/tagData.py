from dataclasses import dataclass
from datetime import datetime

@dataclass
class TagPosition:
    X: float
    Y: float
    Z: float
    QF: int

@dataclass
class AnchorPosition:
    AnchorID: str
    X: float
    Y: float
    Z: float
    MetersFromTag: float

@dataclass
class TagData:
    TimeStamp = datetime
    TagPosition = TagPosition
    AnchorPositions = list[AnchorPosition]
