from .weapon_base import VersatileWeapon
from .damage_modifiers import DamageModifier
from .damage_modifiers.fighting_styles import GreatWeaponFighting

class Longsword(VersatileWeapon):
    default_mastery = []
    gui_name = "Longsword"

    def __init__(self, owner):
        super().__init__(owner, "Longsword", damage_type= "Slashing", base_dice="1d8")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"
