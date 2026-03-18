from .damage_modifiers import DamageModifier

class Sharpshooter(DamageModifier):
    category = "Feat"
    gui_name = "Sharpshooter"

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus-5

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 10
        return damage

class GreatWeaponMaster(DamageModifier):
    category = "Feat"
    gui_name = "GWM"

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus-5

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 10
        return damage

class CrossbowExpert(DamageModifier):
    category = "Feat"
    gui_name = "CBE"

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.weapon_type == "Ranged, Light":
            return damage + (3.5 + weapon.owner.get_stat_mod(context.stat))
        return damage