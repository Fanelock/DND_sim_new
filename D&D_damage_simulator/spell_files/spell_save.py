from .spell_base import Spell
from utils.math_helpers import dice_avg, parse_dice, clamp01


class SpellSave(Spell):
    gui_name = "Spell Save"

    def __init__(self, owner):
        super().__init__(owner, "Spell Save")

    def expected_damage(self, save_mod, context):
        stat_mod = self.owner.get_stat_mod(context.stat)
        prof_bonus = self.owner.get_prof_bonus()
        spell_dc = 8 + stat_mod + prof_bonus

        # Probability the target fails the save
        # Roll needed to succeed: spell_dc - save_mod
        # Rolls are 1-20; nat 1 always fails, nat 20 always succeeds
        rolls_that_fail = spell_dc - save_mod - 1
        p_fail = clamp01(rolls_that_fail / 20.0)
        p_succeed = 1.0 - p_fail

        # Saving throws have no critical failures in D&D 5e/2024 rules
        dice_type = context.dice
        if hasattr(self, "get_dice_for_attack"):
            dice_type = self.get_dice_for_attack(context)

        num, die = parse_dice(dice_type)
        full = num * dice_avg[die] + context.damage_bonus
        half = full / 2.0

        # On fail: full damage; on succeed: half damage (standard spell save)
        expected = p_fail * full + p_succeed * half

        return {
            "num_attacks": 1,
            "disadvantage": expected,
            "normal": expected,
            "advantage": expected,
            "debug": {
                "damage": {
                    "miss": half,
                    "hit": full,
                    "crit": full  # no crits on saves
                },
                "breakdown": {
                    "disadvantage": {"hit": p_fail, "crit": 0.0, "miss": p_succeed},
                    "normal": {"hit": p_fail, "crit": 0.0, "miss": p_succeed},
                    "advantage": {"hit": p_fail, "crit": 0.0, "miss": p_succeed},
                }
            }
        }

    def __str__(self):
        return f"{self.name}"
