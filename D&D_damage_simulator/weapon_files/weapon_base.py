import random as rd
from abc import ABC, abstractmethod
from .damage_modifiers import DamageModifier

dice_avg = {
    "d4": 2.5, "d6": 3.5, "d8": 4.5,
    "d10": 5.5, "d12": 6.5
}

def parse_dice(notation):
    num, die = notation.lower().split("d")
    return int(num), "d" + die

def hit_probabilities(ac, to_hit_bonus):
    p_crit = 0.05
    p_hit = max(0, min(1, (21 + to_hit_bonus - ac) / 20))
    p_hit_normal = max(0, p_hit - p_crit)

    p_hit_adv = 1 - (1 - p_hit_normal)**2
    p_hit_dis = p_hit_normal**2

    return {
        "normal": p_hit_normal,
        "advantage": p_hit_adv,
        "disadvantage": p_hit_dis,
        "crit": p_crit,
        "miss": 1 - p_hit
    }

class Weapon(ABC):
    default_mastery = []

    def __init__(self, owner, name, weapon_type, dice_type):
        self.owner = owner
        self.name = name
        self.weapon_type = weapon_type
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

        for m in applied_modifiers:
            to_hit = m.modify_attack_bonus(self, to_hit, context)

        probs = hit_probabilities(ac, to_hit)
        if hasattr(self, "get_dice_for_attack"):
            self.dice_type = self.get_dice_for_attack(context)
        else:
            self.dice_type = self.dice_type

        num, die = parse_dice(self.dice_type)
        normal = num * dice_avg[die] + stat_mod
        crit = normal + num * dice_avg[die]
        miss = 0

        for m in applied_modifiers:
            normal = m.modify_attack_damage(self, normal, hit=True, crit=False, context=context)
            crit = m.modify_attack_damage(self, crit, hit=True, crit=True, context=context)
            miss = m.modify_attack_damage(self, miss, hit=False, crit=False, context=context)

        return {
            "normal": probs["normal"] * normal + probs["crit"] * crit,
            "advantage": probs["advantage"] * normal + probs["crit"] * crit,
            "disadvantage": probs["disadvantage"] * normal + probs["crit"] * crit,
            "miss": probs["miss"] * miss,
            "probabilities": probs,
        }

    @abstractmethod
    def __str__(self):
        pass

class VersatileWeapon(Weapon):
    default_mastery = []

    def __init__(self, owner, name, base_dice="1d8"):
        super().__init__(owner, name, "Versatile", base_dice)
        self.base_dice = base_dice
        self.dmg = 0
        self.supports_sneak_attack = False

    def get_dice_for_attack(self, context):
        if context.two_handed and self.base_dice == "1d8":
            return "1d10"
        return self.base_dice

    def __str__(self):
        return f"{self.name} ({self.weapon_type}): {self.dice_type} damage"