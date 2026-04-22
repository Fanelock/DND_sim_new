extra_attack_table = [
    (20, 4),
    (11, 3),
    (5,  2),
    (1,  1),
]


def fighter_modifier(lvl: int) -> int:
    for min_lvl, attacks in extra_attack_table:
        if lvl >= min_lvl:
            return attacks
    return 1
