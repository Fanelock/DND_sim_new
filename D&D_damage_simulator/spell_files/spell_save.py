from .spell_base import Spell

dice_avg = {
    "d4": 2.5, "d6": 3.5, "d8": 4.5,
    "d10": 5.5, "d12": 6.5
}

def parse_dice(notation):
    num, die = notation.lower().split("d")
    return int(num), "d" + die

def clamp01(x):
    return max(0.0, min(1.0, x))

class SpellSave(Spell):
    gui_name = "Spell Save"

    def __init__(self, owner):
        super().__init__(owner, "Spell Save")

    def expected_damage(self, save_mod, context):
        stat_mod = self.owner.get_stat_mod(context.stat)
        prof_bonus = self.owner.get_prof_bonus()
        spell_dc = 8 + stat_mod + prof_bonus

        max_fail_roll = spell_dc - save_mod - 1
        p_fail_total = clamp01(max_fail_roll / 20.0)

        p_crit = 0.05 if p_fail_total > 0 else 0.0
        p_fail_normal = max(0.0, p_fail_total-p_crit)
        p_succeed = 1.0 - p_fail_normal - p_crit

        dice_type = context.dice
        if hasattr(self, "get_dice_for_attack"):
            dice_type = self.get_dice_for_attack(context)

        num, die = parse_dice(dice_type)
        full = num * dice_avg[die] + context.damage_bonus
        crit = 2 * (num * dice_avg[die]) + context.damage_bonus
        half = full / 2.0

        expected = p_fail_normal * full + p_succeed * half + crit * p_crit

        return {
            "num_attacks": 1,
            "disadvantage": expected,
            "normal": expected,
            "advantage": expected,
            "debug": {
                "damage": {
                    "miss": half,
                    "hit": full,
                    "crit": crit
                },
                "breakdown": {
                    "disadvantage": {"hit": p_fail_normal, "crit": p_crit, "miss": p_succeed},
                    "normal": {"hit": p_fail_normal, "crit": p_crit, "miss": p_succeed},
                    "advantage": {"hit": p_fail_normal, "crit": p_crit, "miss": p_succeed},
                }
            }
        }

    def __str__(self):
        return f"{self.name}"