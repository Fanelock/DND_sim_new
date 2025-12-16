from .weapon_base import Weapon
from .damage_modifiers import DamageModifier
from .damage_modifiers.fighting_styles import GreatWeaponFighting

class Longbow(Weapon):
    default_mastery = []

    def __init__(self, owner):
        super().__init__(owner, "Longbow", "Ranged", "1d8")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"