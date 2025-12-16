from .damage_modifiers import DamageModifier

class WeaponMasteryGraze(DamageModifier):
    is_mastery = True

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage
        return weapon.owner.dex if weapon.weapon_type == "finesse" else weapon.owner.str