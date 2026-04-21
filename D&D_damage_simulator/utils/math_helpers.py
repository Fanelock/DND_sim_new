# Shared math utilities for damage calculations

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
