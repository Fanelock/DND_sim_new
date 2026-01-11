from .weapon_base import Weapon
from .damage_modifiers.weapon_masteries import WeaponMasteryGraze

class Shortsword(Weapon):
    default_mastery = []
    gui_name = "Shortsword"

    def __init__(self, owner):
        super().__init__(owner, "Shortsword", "Light", "Piercing", "1d6")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"