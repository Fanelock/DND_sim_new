from .weapon_base import Weapon
from .damage_modifiers import DamageModifier

class CrossbowHand(Weapon):
    default_mastery = []
    gui_name = "Hand Crossbow"

    def __init__(self, owner):
        super().__init__(owner, "Crossbow Hand", "Ranged, Light", "Piercing", "1d6")

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type}"