from abc import ABC, abstractmethod

class DamageModifier:
    category = "Unnamed Category"
    priority = 50
    applies_to_spell = False

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        return damage
