from .damage_modifiers import DamageModifier
import math


class DivineStrike(DamageModifier):
    category = "Class Feature"
    gui_name = "Divine Strike"
    priority = 50
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.owner.lvl > 6:
            bonus = (4.5 if weapon.owner.lvl <= 13 else 9)
            if crit:
                bonus *= 2
            return damage + bonus
        return damage


class HuntersMark(DamageModifier):
    category = "Class Feature Manual"
    gui_name = "Hunter's Mark"
    priority = 10
    applies_to_spell = True

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            bonus = 3.5
            if crit:
                bonus *= 2
            return damage + bonus
        return damage


class Rage(DamageModifier):
    category = "Class Feature"
    gui_name = "Rage"
    priority = 10
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            # +2 at level 1, +3 at level 9, +4 at level 16 (2024 rules)
            lvl = weapon.owner.lvl
            if lvl >= 16:
                bonus = 4
            elif lvl >= 9:
                bonus = 3
            else:
                bonus = 2
            return damage + bonus
        return damage


class SneakAttack(DamageModifier):
    category = "Class Feature"
    gui_name = "Sneak Attack"
    priority = 50
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if not getattr(context, "allow_sneak", True):
            return damage

        if hit and weapon.weapon_type in ("Finesse", "Ranged", "Light"):
            bonus = (3.5 * math.ceil(weapon.owner.lvl / 2))
            if crit:
                bonus *= 2
            return damage + bonus
        return damage


class PrimalStrike(DamageModifier):
    category = "Class Feature"
    gui_name = "Primal Strike"
    priority = 50
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.owner.lvl > 6:
            bonus = (4.5 if weapon.owner.lvl <= 14 else 9)
            if crit:
                bonus *= 2
            return damage + bonus
        return damage


class DivineSmite(DamageModifier):
    category = "Class Feature Manual"
    gui_name = "Divine Smite"
    priority = 50
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        # Simplified: assumes 2nd-level spell slot (2d8 = 9 avg).
        # Divine Smite scales with slot level but slot choice is not modelled here.
        if hit:
            bonus = 9
            if crit:
                bonus *= 2
            return damage + bonus
        return damage


class AgonizingBlast(DamageModifier):
    category = "Class Feature Manual"
    gui_name = "Agonizing Blast"
    priority = 10
    applies_to_spell = True

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        # weapon may be a Spell instance here (Eldritch Blast) — use get_stat_mod for safety
        if hit:
            cha_mod = weapon.owner.get_stat_mod("cha")
            return damage + cha_mod
        return damage


def warlock_modifier(weapon):
    if weapon.owner.lvl < 5:
        return 1
    return 2 if weapon.owner.lvl <= 11 else 3


class ThirstingBlade(DamageModifier):
    """Handled via num_attacks in weapon_base; modifier kept for detection."""
    category = "Class Feature Manual"
    gui_name = "Thirsting Blade"
    priority = 20
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        # Attack count multiplication is handled in weapon_base.expected_damage
        return damage


class Multiattack(DamageModifier):
    """Handled via num_attacks in weapon_base; modifier kept for detection."""
    category = "Class Feature"
    gui_name = "Multiattack"
    priority = 20
    applies_to_spell = False

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        # Attack count multiplication is handled in weapon_base.expected_damage
        return damage
