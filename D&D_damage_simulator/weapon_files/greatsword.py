from .weapon_base import Weapon
from .damage_modifiers.weapon_masteries import WeaponMasteryGraze

class Greatsword(Weapon):
    default_mastery = [WeaponMasteryGraze]

    def __init__(self, owner):
        super().__init__(owner, "Greatsword", "Two-Handed", "2d6")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"