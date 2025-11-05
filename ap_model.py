
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any

@dataclass
class APModel:
    mt: Dict[str, Any] = field(default_factory=dict)
    mt_minus1: Dict[str, Any] = field(default_factory=dict)
    mt_plus1: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, Any]] = field(default_factory=list)

    def to_json(self):
        return asdict(self)

    def set_element(self, timeframe: str, key: str, value: Any):
        if timeframe not in ('mt', 'mt_minus1', 'mt_plus1'):
            raise ValueError('timeframe must be mt | mt_minus1 | mt_plus1')
        target = getattr(self, timeframe)
        target[key] = value

    def add_relation(self, src: str, dst: str, label: str):
        self.relations.append({'src': src, 'dst': dst, 'label': label})
