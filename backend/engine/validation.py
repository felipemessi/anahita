from dataclasses import dataclass

from .types import Ability

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]

def validate_multiclass(
    current_classes: list[str],
    new_class: str,
    ability_scores: dict[Ability, int],
    requirements: dict[str, dict[Ability, int]],
) -> ValidationResult:
    """Validate if a character can multiclass into a new class."""
    errors = []

    for c in current_classes:
        req = requirements.get(c)
        if req:
            for ab, score in req.items():
                if ability_scores.get(ab, 0) < score:
                    errors.append(f"Requires {score} {ab.value.upper()} to multiclass out of {c}.")

    new_req = requirements.get(new_class)
    if new_req:
        for ab, score in new_req.items():
            if ability_scores.get(ab, 0) < score:
                errors.append(f"Requires {score} {ab.value.upper()} to multiclass into {new_class}.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
