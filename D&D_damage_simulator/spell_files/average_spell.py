from .spell_base import Spell

class SpellAttack(Spell):
    gui_name = "Average Spell"

    def __init__(self, owner):
        super().__init__(owner, "Average Spell")

    def __str__(self):
        return f"{self.name}"