import pkgutil
import importlib
import inspect

for _, module_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_name}")

from . import damage_modifiers
from .weapon_base import Weapon

__all__ = ["Weapon", "damage_modifiers"]