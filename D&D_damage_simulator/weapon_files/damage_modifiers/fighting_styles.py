from .damage_modifiers import DamageModifier

class GreatWeaponFighting(DamageModifier):
    category = "Fighting Style"
    gui_name = "GWF"
    priority = 10
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 2
        return damage

class Dueling(DamageModifier):
    category = "Fighting Style"
    gui_name = "Dueling"
    priority = 10
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and not context.two_handed:
            return damage + 2
        return damage

class Archery(DamageModifier):
    category = "Fighting Style"
    gui_name = "Archery"
    priority = 10
    applies_to_spell = False

    def modify_attack_bonus(self, weapon, bonus, context, **kwargs):
        return bonus + 2

extra_attack_table = {
    1: 1,   # optional: level 1–4
    5: 2,   # level 5–10
    11: 3,  # level 11–19
    20: 4   # level 20
}

def fighter_modifier(weapon):
    for lvl_req in sorted(extra_attack_table, reverse=True):
        if weapon.owner.lvl >= lvl_req:
            return extra_attack_table[lvl_req]
    return 1

class TwoWeaponFighting(DamageModifier):
    category = "Fighting Style"
    gui_name = "TWF"
    priority = 30
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            actual_dmg = damage / fighter_modifier(weapon)
            return damage + actual_dmg
        return damage
