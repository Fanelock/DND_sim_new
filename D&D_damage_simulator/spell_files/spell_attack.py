from .spell_base import Spell

class SpellAttack(Spell):
    gui_name = "Spell Attack"

    def __init__(self, owner):
        super().__init__(owner, "Spell Attack")

    def __str__(self):
        return f"{self.name}"