from abc import ABC, abstractmethod

class DamageModifier:
    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        return damage
