import random as rd
from abc import ABC, abstractmethod

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

class Spell(ABC):
    default_mastery = []

    def __init__(self, owner, name):
        self.owner = owner
        self.name = name

    def expected_damage(self, ac, context):

        stat_mod = self.owner.get_stat_mod(context.stat)
        prof_bonus = self.owner.get_prof_bonus()
        to_hit = stat_mod + prof_bonus + context.magic_bonus

        dice_type = context.dice

        if hasattr(self, "get_dice_for_attack"):
            dice_type = self.get_dice_for_attack(context)

        num, die = parse_dice(dice_type)
        normal = num * dice_avg[die] + context.magic_bonus + context.damage_bonus

        crit = normal + num * dice_avg[die]
        miss = 0


        num_attacks = 1

        d_n, d_c, d_m = dis_hit_probs(ac, to_hit)
        n_n, n_c, n_m = base_hit_probs(ac, to_hit)
        a_n, a_c, a_m = adv_hit_probs(ac, to_hit)

        dis_ev = d_n * normal + d_c * crit + d_m * miss
        normal_ev = n_n * normal + n_c * crit + n_m * miss
        adv_ev = a_n * normal + a_c * crit + a_m * miss

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