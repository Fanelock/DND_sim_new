from .damage_modifiers import DamageModifier

class Sharpshooter(DamageModifier):
    category = "Feat"

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus-5

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 10
        return damage

class GreatWeaponMaster(DamageModifier):
    category = "Feat"

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus-5

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 10
        return damage