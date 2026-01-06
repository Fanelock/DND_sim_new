from .damage_modifiers import DamageModifier
import math

class DivineStrike(DamageModifier):
    category = "ClassFeature"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.owner.lvl > 6:
            return damage + (4.5 if weapon.owner.lvl <= 13 else 9)
        return damage

class HuntersMark(DamageModifier):
    category = "ClassFeature"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 3.5
        return damage

class Rage(DamageModifier):
    category = "ClassFeature"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + min(4, 2 + (max(0, weapon.owner.lvl - 1) // 8))
        return damage

class SneakAttack(DamageModifier):
    category = "ClassFeature"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.weapon_type in ("Finesse", "Ranged", "Light"):
            return damage +(3.5 * math.ceil(weapon.owner.level / 2))
        return damage

class PrimalStrike(DamageModifier):
    category = "ClassFeature"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.owner.lvl > 6:
            return damage + (4.5 if weapon.owner.lvl <= 14 else 9)
        return damage