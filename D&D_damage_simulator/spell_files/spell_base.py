from abc import ABC, abstractmethod
from utils.math_helpers import (
    dice_avg, parse_dice,
    base_hit_probs, adv_hit_probs, dis_hit_probs
)


class Spell(ABC):
    default_mastery = []

    def __init__(self, owner, name):
        self.owner = owner
        self.name = name

    def expected_damage(self, ac, context):
        stat_mod = self.owner.get_stat_mod(context.stat)
        prof_bonus = self.owner.get_prof_bonus()
        # magic_bonus applies to the attack roll only, not spell damage
        to_hit = stat_mod + prof_bonus + context.magic_bonus

        dice_type = context.dice
        if hasattr(self, "get_dice_for_attack"):
            dice_type = self.get_dice_for_attack(context)

        num, die = parse_dice(dice_type)
        normal = num * dice_avg[die] + context.damage_bonus
        crit = normal + num * dice_avg[die]
        miss = 0

        num_attacks = 1

        d_n, d_c, d_m = dis_hit_probs(ac, to_hit)
        n_n, n_c, n_m = base_hit_probs(ac, to_hit)
        a_n, a_c, a_m = adv_hit_probs(ac, to_hit)

        dis_ev = num_attacks * (d_n * normal + d_c * crit + d_m * miss)
        normal_ev = num_attacks * (n_n * normal + n_c * crit + n_m * miss)
        adv_ev = num_attacks * (a_n * normal + a_c * crit + a_m * miss)

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
