from .damage_modifiers import DamageModifier


class GreatWeaponFighting(DamageModifier):
    category = "Fighting Style"
    gui_name = "GWF"
    priority = 10
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + 1
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


class TwoWeaponFighting(DamageModifier):
    """Adds one extra off-hand attack (no ability modifier on damage) on top of main attacks.
    The actual extra attack EV is computed in weapon_base.expected_damage."""
    category = "Fighting Style"
    gui_name = "TWF"
    priority = 30
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        # No-op: off-hand attack is handled directly in weapon_base.expected_damage
        return damage
