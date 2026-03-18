from .damage_modifiers import DamageModifier

class WeaponMasteryGraze(DamageModifier):
    is_mastery = True
    category = "Mastery"
    priority = 10
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage
        stat_mod = weapon.owner.get_stat_mod(context.stat)
        return max(0, stat_mod)

class WeaponMasteryNick(DamageModifier):
    is_mastery = True
    category = "Mastery"
    priority = 100
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        return damage