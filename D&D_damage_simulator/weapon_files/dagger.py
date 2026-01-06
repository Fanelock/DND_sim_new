from .weapon_base import Weapon
from .damage_modifiers.weapon_masteries import WeaponMasteryNick

class Dagger(Weapon):
    default_mastery = [WeaponMasteryNick]
    gui_name = "Dagger"

    def __init__(self, owner):
        super().__init__(owner, "Dagger", "Light", "Piercing", "1d4")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"