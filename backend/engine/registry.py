from .class_handlers.base import ClassHandler

_CLASS_HANDLERS: dict[str, type[ClassHandler]] = {}


def register_class_handler(class_id: str, handler: type[ClassHandler]) -> None:
    _CLASS_HANDLERS[class_id] = handler


def get_class_handler(class_id: str) -> type[ClassHandler] | None:
    return _CLASS_HANDLERS.get(class_id)
