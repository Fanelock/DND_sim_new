from .weapon_base import Weapon
from .damage_modifiers.weapon_masteries import WeaponMasteryGraze

class Greataxe(Weapon):
    default_mastery = [WeaponMasteryGraze]
    gui_name = "Greataxe"

    def __init__(self, owner):
        super().__init__(owner, "Greataxe", "Two-Handed", "Slashing", "2d6")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"