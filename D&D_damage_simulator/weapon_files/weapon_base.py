from abc import ABC, abstractmethod
from .damage_modifiers import DamageModifier
from .damage_modifiers.class_features import Multiattack, warlock_modifier, ThirstingBlade
from .damage_modifiers.fighting_styles import TwoWeaponFighting
from .damage_modifiers.weapon_masteries import WeaponMasteryGraze, WeaponMasteryNick
from utils.math_helpers import (
    dice_avg, parse_dice, clamp01,
    base_hit_probs, adv_hit_probs, dis_hit_probs
)


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

        # Resolve num_attacks first so Graze can use the final value
        num_attacks = 1
        if any(isinstance(m, Multiattack) for m in applied_modifiers):
            num_attacks = self.owner.class_.get_attack_count(self)
        if any(isinstance(m, ThirstingBlade) for m in applied_modifiers):
            num_attacks = warlock_modifier(self)
        # TWF fighting style modifier: off-hand attack WITH stat_mod (PHB rule for the style)
        has_twf_style = any(isinstance(m, TwoWeaponFighting) for m in applied_modifiers)
        # use_twf context flag: bare off-hand attack WITHOUT stat_mod (available to anyone)
        has_twf_basic = getattr(context, "use_twf", False)
        # Either source adds the extra attack
        has_twf = has_twf_style or has_twf_basic
        if has_twf:
            num_attacks += 1

        # Apply per-attack damage modifiers (excluding attack-count modifiers)
        skip_types = (Multiattack, ThirstingBlade, TwoWeaponFighting)
        for m in applied_modifiers:
            if isinstance(m, skip_types):
                continue
            miss = m.modify_attack_damage(self, miss, hit=False, crit=False, context=context)
            normal = m.modify_attack_damage(self, normal, hit=True, crit=False, context=context)
            crit = m.modify_attack_damage(self, crit, hit=True, crit=True, context=context)

        if has_twf:
            if has_twf_style:
                # TWF fighting style: off-hand INCLUDES stat_mod (that's the benefit of the style)
                offhand_normal = num * dice_avg[die] + stat_mod + context.magic_bonus + context.damage_bonus
            else:
                # Basic TWF (checkbox only): off-hand does NOT add stat_mod
                offhand_normal = num * dice_avg[die] + context.magic_bonus + context.damage_bonus
            offhand_crit = offhand_normal + num * dice_avg[die]
            for m in applied_modifiers:
                if isinstance(m, skip_types):
                    continue
                offhand_normal = m.modify_attack_damage(self, offhand_normal, hit=True, crit=False, context=context)
                offhand_crit = m.modify_attack_damage(self, offhand_crit, hit=True, crit=True, context=context)
        else:
            offhand_normal = offhand_crit = 0

        # Graze: on a miss, deal stat_mod damage per attack
        has_graze = any(isinstance(m, WeaponMasteryGraze) for m in applied_modifiers)
        if has_graze:
            miss = max(0, stat_mod) * num_attacks

        d_n, d_c, d_m = dis_hit_probs(ac, to_hit)
        n_n, n_c, n_m = base_hit_probs(ac, to_hit)
        a_n, a_c, a_m = adv_hit_probs(ac, to_hit)

        main_attacks = num_attacks - (1 if has_twf else 0)

        def ev(pn, pc, pm, n_hit, n_crit, n_miss, off_n, off_c, main_count):
            main_ev = main_count * (pn * n_hit + pc * n_crit + pm * n_miss)
            off_ev = (pn * off_n + pc * off_c) if has_twf else 0
            return main_ev + off_ev

        dis_ev = ev(d_n, d_c, d_m, normal, crit, miss, offhand_normal, offhand_crit, main_attacks)
        normal_ev = ev(n_n, n_c, n_m, normal, crit, miss, offhand_normal, offhand_crit, main_attacks)
        adv_ev = ev(a_n, a_c, a_m, normal, crit, miss, offhand_normal, offhand_crit, main_attacks)

        if any(isinstance(m, WeaponMasteryNick) for m in applied_modifiers):
            nick_weapon_normal = num * dice_avg[die] + stat_mod
            nick_weapon_crit = nick_weapon_normal + num * dice_avg[die]
            dis_ev += d_n * nick_weapon_normal + d_c * nick_weapon_crit
            normal_ev += n_n * nick_weapon_normal + n_c * nick_weapon_crit
            adv_ev += a_n * nick_weapon_normal + a_c * nick_weapon_crit

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


class VersatileWeapon(Weapon):
    """A weapon that can be used one-handed (base_dice) or two-handed (upgraded dice)."""

    _versatile_upgrade = {
        "1d6": "1d8",
        "1d8": "1d10",
    }

    def __init__(self, owner, name, damage_type, base_dice):
        super().__init__(owner, name, "Versatile", damage_type, base_dice)
        self.base_dice = base_dice

    def get_dice_for_attack(self, context):
        if context.two_handed:
            return self._versatile_upgrade.get(self.base_dice, self.base_dice)
        return self.base_dice
