from .damage_modifiers import DamageModifier

class DivineStrike(DamageModifier):
    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 4.5
        return damage