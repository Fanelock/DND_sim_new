from .damage_modifiers import DamageModifier


class WeaponMasteryGraze(DamageModifier):
    """On a miss, deal your ability modifier in damage (minimum 0) per attack.
    The scaling by num_attacks is handled in weapon_base.expected_damage after
    num_attacks is fully resolved."""
    is_mastery = True
    category = "Mastery"
    priority = 10
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        # Miss damage is computed directly in weapon_base; this is a no-op there.
        return damage


class WeaponMasteryNick(DamageModifier):
    is_mastery = True
    category = "Mastery"
    priority = 100
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        return damage
