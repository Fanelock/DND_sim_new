import pkgutil
import importlib
import inspect

for _, module_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_name}")

from .attack_count import fighter_modifier

__all__ = ["fighter_modifier"]
