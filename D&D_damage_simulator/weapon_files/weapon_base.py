import random as rd
from abc import ABC, abstractmethod
from .damage_modifiers import DamageModifier
from .damage_modifiers.class_features import Multiattack, warlock_modifier, ThirstingBlade
from .damage_modifiers.class_features import fighter_modifier, attack_count
from .damage_modifiers.fighting_styles import TwoWeaponFighting
from .damage_modifiers.weapon_masteries import WeaponMasteryGraze

dice_avg = {
    "d4": 2.5, "d6": 3.5, "d8": 4.5,
    "d10": 5.5, "d12": 6.5
}

def parse_dice(notation):
    num, die = notation.lower().split("d")
    return int(num), "d" + die

def clamp01(x):
    return max(0.0, min(1.0, x))

def base_hit_probs(ac, to_hit):
    p_crit = 0.05
    p_hit = clamp01((21 + to_hit - ac) / 20)
    p_normal = max(0.0, p_hit - p_crit)
    p_miss = 1.0 - p_hit
    return p_normal, p_crit, p_miss

def adv_hit_probs(ac, to_hit):
    n, c, m = base_hit_probs(ac, to_hit)

    # crit if either die crits
    p_crit = 1 - (1 - c) ** 2

    # miss only if both miss
    p_miss = m ** 2

    # otherwise it's a normal hit
    p_normal = 1 - p_crit - p_miss
    return p_normal, p_crit, p_miss

def dis_hit_probs(ac, to_hit):
    n, c, m = base_hit_probs(ac, to_hit)

    # crit only if both crit
    p_crit = c ** 2

    # hit only if both hit
    p_hit = (n + c) ** 2
    p_normal = p_hit - p_crit
    p_miss = 1 - p_hit

    return p_normal, p_crit, p_miss

class Weapon(ABC):
    default_mastery = []

    def __init__(self, owner, name, weapon_type, damage_type, dice_type):
        self.owner = owner
        self.name = name
        self.weapon_type = weapon_type
        self.damage_type = damage_type
        self.dice_type = dice_type

    def expected_damage(self, ac, context):

        stat_mod = self.owner.get_stat_mod(context.stat)
        prof_bonus = self.owner.get_prof_bonus()
        to_hit = stat_mod + prof_bonus + context.magic_bonus

        all_modifiers = (
                [m() for m in self.default_mastery] +
                self.owner.get_modifiers()
        )

        applied_modifiers = [
            m for m in all_modifiers
            if context.use_mastery or not getattr(m, "is_mastery", False)
        ]

        applied_modifiers.sort(key=lambda m: getattr(m, "priority", 50))

        for m in applied_modifiers:
            to_hit = m.modify_attack_bonus(self, to_hit, context)

        if hasattr(self, "get_dice_for_attack"):
            self.dice_type = self.get_dice_for_attack(context)

        num, die = parse_dice(self.dice_type)
        normal = num * dice_avg[die] + stat_mod + context.magic_bonus + context.damage_bonus
        crit = normal + num * dice_avg[die]
        miss = 0

        for m in applied_modifiers:
            miss = m.modify_attack_damage(self, miss, hit=False, crit=False, context=context)
            normal = m.modify_attack_damage(self, normal, hit=True, crit=False, context=context)
            crit = m.modify_attack_damage(self, crit, hit=True, crit=True, context=context)

        num_attacks = 1

        if any(isinstance(m, Multiattack) for m in applied_modifiers):
            num_attacks = attack_count(self)

        if any(isinstance(m, TwoWeaponFighting) for m in applied_modifiers):
            num_attacks += 1

        if any(isinstance(m, ThirstingBlade) for m in applied_modifiers):
            num_attacks = warlock_modifier(self)

        if any(isinstance(m, WeaponMasteryGraze) for m in applied_modifiers):
            miss *= num_attacks

        d_n, d_c, d_m = dis_hit_probs(ac, to_hit)
        n_n, n_c, n_m = base_hit_probs(ac, to_hit)
        a_n, a_c, a_m = adv_hit_probs(ac, to_hit)

        dis_ev = d_n * normal + d_c * crit + d_m * miss
        normal_ev = n_n * normal + n_c * crit + n_m * miss
        adv_ev = a_n * normal + a_c * crit + a_m * miss

        if any(m.__class__.__name__ == "WeaponMasteryNick" for m in applied_modifiers):
            _normal = 2.5 + context.magic_bonus
            _crit = 5 + context.magic_bonus
            dis_ev += d_n * _normal + d_c * _crit
            normal_ev += n_n * _normal + n_c * _crit
            adv_ev += a_n * _normal + a_c * _crit

        return {
            "num_attacks": num_attacks,

            "disadvantage": dis_ev,
            "normal": normal_ev,
            "advantage": adv_ev,

            "debug": {
                "damage": {
                    "miss": miss,
                    "hit": normal,
                    "crit": crit
                },
                "breakdown": {
                    "disadvantage": {"hit": d_n, "crit": d_c, "miss": d_m},
                    "normal": {"hit": n_n, "crit": n_c, "miss": n_m},
                    "advantage": {"hit": a_n, "crit": a_c, "miss": a_m},
                }
            }
        }

    @abstractmethod
    def __str__(self):
        pass

class VersatileWeapon(Weapon, ABC):
    default_mastery = []

    def __init__(self, owner, name, damage_type, base_dice="1d8"):
        super().__init__(owner, name, "Versatile", damage_type, base_dice)
        self.base_dice = base_dice
        self.dmg = 0
        self.supports_sneak_attack = False

    def get_dice_for_attack(self, context):
        if context.two_handed and self.base_dice == "1d8":
            return "1d10"
        return self.base_dice

    @abstractmethod
    def __str__(self):
        pass