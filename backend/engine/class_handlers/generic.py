
from ..types import CharacterContext
from .base import ClassHandler


class GenericClassHandler(ClassHandler):
    """
    A generic handler that parses mechanical effects defined as strings in the database.
    """
    def __init__(self, effects_vocabulary: list[str]):
        self.effects = effects_vocabulary

    def modify_ac(self, base_ac: int, context: CharacterContext) -> int:
        for ef in self.effects:
            if ef.startswith("bonus_ac:"):
                try:
                    val = int(ef.split(":")[1])
                    base_ac += val
                except ValueError:
                    pass
        return base_ac

    def modify_attack(self, base_bonus: int, context: CharacterContext) -> int:
        # Simplistic example for attack bonuses
        for ef in self.effects:
            if ef.startswith("bonus_attack:"):
                try:
                    val = int(ef.split(":")[1])
                    base_bonus += val
                except ValueError:
                    pass
        return base_bonus
