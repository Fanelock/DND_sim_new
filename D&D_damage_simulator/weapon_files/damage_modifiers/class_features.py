from locale import locale_alias

from class_files.fighter.fighter_class import Fighter
from .damage_modifiers import DamageModifier
import math

class DivineStrike(DamageModifier):
    category = "Class Feature"
    gui_name = "Divine Strike"
    priority = 50

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

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + min(4, 2 + (max(0, weapon.owner.lvl - 1) // 8))
        return damage

class SneakAttack(DamageModifier):
    category = "Class Feature"
    gui_name = "Sneak Attack"
    priority = 50

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

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            bonus = 9
            if crit:
                bonus *= 2
            return damage + bonus
        return damage

class AgonizingBlast(DamageModifier):
    category = "Class Feature"
    gui_name = "Agonizing Blast"
    priority = 10

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit:
            return damage + weapon.owner.cha
        return damage

def warlock_modifier(weapon):
    return 2 if weapon.owner.lvl <= 11 else 3

class ThirstingBlade(DamageModifier):
    category = "Class Feature Manual"
    gui_name = "Thirsting Blade"
    priority = 20

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.owner.class_.name == "Warlock":
            if weapon.owner.lvl >= 5:
                return damage * warlock_modifier(weapon)
            return damage
        return damage

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

class Multiattack(DamageModifier):
    category = "Class Feature"
    gui_name = "Multiattack"
    priority = 20

    def modify_attack_damage(self, weapon, damage, hit, crit, context, **kwargs):
        if hit and weapon.owner.lvl >= 5:
            if weapon.owner.class_.name == "Fighter":
                return damage * fighter_modifier(weapon)
            return damage * 2
        return damage

def attack_count(weapon):
    if weapon.owner.lvl >= 5:
        if weapon.owner.class_.name == "Fighter":
            return fighter_modifier(weapon)
        return 2
    return 1


