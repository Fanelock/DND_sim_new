from .weapon_base import VersatileWeapon
from .damage_modifiers import DamageModifier
from .damage_modifiers.fighting_styles import GreatWeaponFighting

class Warhammer(VersatileWeapon):
    default_mastery = []
    gui_name = "Warhammer"

    def __init__(self, owner):
        super().__init__(owner, "Warhammer", damage_type="Bludgeoning", base_dice="1d8")
        self.damage_type = "bludgeoning"

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"