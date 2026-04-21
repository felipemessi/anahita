from abc import ABC, abstractmethod

from ..types import CharacterContext


class ClassHandler(ABC):
    @abstractmethod
    def modify_ac(self, base_ac: int, context: CharacterContext) -> int:
        pass

    @abstractmethod
    def modify_attack(self, base_bonus: int, context: CharacterContext) -> int:
        pass
