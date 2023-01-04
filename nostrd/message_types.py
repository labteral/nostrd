from enum import Enum


class MessageTypes(Enum):
    EVENT = 'EVENT'
    REQUEST = 'REQ'
    CLOSE = 'CLOSE'

    @classmethod
    @property
    def values(cls):
        return [_.value for _ in cls.__members__.values()]
