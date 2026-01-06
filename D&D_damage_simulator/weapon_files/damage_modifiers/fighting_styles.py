from .damage_modifiers import DamageModifier

class GreatWeaponFighting(DamageModifier):
    category = "FightingStyle"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 2
        return damage

class Dueling(DamageModifier):
    category = "FightingStyle"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and not context.two_handed:
            return damage + 2
        return damage

class Archery(DamageModifier):
    category = "FightingStyle"

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus + 2
