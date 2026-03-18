from .spell_base import Spell

class Cantrip_mod(Spell):
    gui_name = "Cantrip+"

    def __init__(self, owner):
        super().__init__(owner, "Cantrip mod")

    def expected_damage(self, ac, context):
        base = super().expected_damage(ac, context)

        stat_mod = self.owner.get_stat_mod(context.stat)

        base['debug']['damage']['hit'] += stat_mod
        base['debug']['damage']['crit'] += stat_mod

        num_attacks = base.get("num_attacks", 1)
        base["disadvantage"] += stat_mod * num_attacks
        base["normal"] += stat_mod * num_attacks
        base["advantage"] += stat_mod * num_attacks

        return base

    def __str__(self):
        return f"{self.name}"