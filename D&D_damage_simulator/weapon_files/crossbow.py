from .weapon_base import Weapon
from .damage_modifiers import DamageModifier


class Crossbow(Weapon):
    default_mastery = []
    gui_name = "Crossbow"

    def __init__(self, owner):
        super().__init__(owner, "Crossbow", "Ranged", "Piercing", "1d8")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"