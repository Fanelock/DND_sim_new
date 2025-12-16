from .damage_modifiers import DamageModifier

class GreatWeaponFighting(DamageModifier):
    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 2
        return damage

class Dueling(DamageModifier):
    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        print("Dueling check, two_handed =", context.two_handed)
        if hit and not context.two_handed:
            return damage + 2
        return damage

class Archery(DamageModifier):
    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus + 2
