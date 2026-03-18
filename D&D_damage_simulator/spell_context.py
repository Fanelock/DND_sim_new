class SpellContext:

    def __init__(self, stat="wis", magic_bonus=0, dice = None, damage_bonus = 0):
        self.stat = stat
        self.magic_bonus = magic_bonus
        self.dice = dice
        self.damage_bonus = damage_bonus