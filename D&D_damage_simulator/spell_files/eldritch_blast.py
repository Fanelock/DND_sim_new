from .spell_base import Spell
from weapon_files.damage_modifiers.class_features import AgonizingBlast, HuntersMark
from utils.attack_count import eldritch_blast_modifier

class Eldritch_blast(Spell):
    gui_name = "Eldritch Blast"

    def __init__(self, owner):
        super().__init__(owner, "Cantrip mod")

    def expected_damage(self, ac, context):
        base = super().expected_damage(ac, context)
        num_beams = eldritch_blast_modifier(self.owner.lvl)

        all_modifiers = list(self.owner.get_modifiers())
        spell_modifiers = [
            m for m in all_modifiers
            if getattr(m, "applies_to_spell", False)
            or isinstance(m, (AgonizingBlast, HuntersMark))
        ]

        hit = base['debug']['damage']['hit']
        crit = base['debug']['damage']['crit']

        for m in spell_modifiers:
            hit = m.modify_attack_damage(self, hit, hit=True, crit=False, context=context)
            crit = m.modify_attack_damage(self, crit, hit=True, crit=True, context=context)

        num_attacks = base.get("num_attacks", 1)
        hit /= num_attacks
        crit /= num_attacks
        hit *= num_beams
        crit *= num_beams

        base['debug']['damage']['hit'] = hit
        base['debug']['damage']['crit'] = crit


        miss = base['debug']['damage']['miss']
        br = base['debug']['breakdown']

        def ev(mode):
            p = br[mode]
            return  (
                    p["hit"] * hit +
                    p["crit"] * crit +
                    p["miss"] * miss
            )

        base["disadvantage"] = ev("disadvantage")
        base["normal"] = ev("normal")
        base["advantage"] = ev("advantage")

        return base

    def __str__(self):
        return f"{self.name}"