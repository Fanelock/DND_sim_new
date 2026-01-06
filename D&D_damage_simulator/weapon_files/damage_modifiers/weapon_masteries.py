from .damage_modifiers import DamageModifier

class WeaponMasteryGraze(DamageModifier):
    is_mastery = True
    category = "Mastery"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage
        return weapon.owner.dex if weapon.weapon_type == "finesse" else weapon.owner.str

class WeaponMasteryNick(DamageModifier):
    is_mastery = True
    category = "Mastery"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        ac = kwargs.get("ac")
        if ac is None:
            ac = getattr(weapon.owner, "ac_target", 15)

        original_mastery_flag = context.use_mastery
        context.use_mastery = False

        second_attack_result = weapon.expected_damage(ac, context)

        context.use_mastery = original_mastery_flag

        extra_damage = second_attack_result.get("normal", 0)
        return damage + extra_damage