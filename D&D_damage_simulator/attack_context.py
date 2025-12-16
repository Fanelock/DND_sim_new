class AttackContext:

    def __init__(self, stat="str", magic_bonus=0, use_mastery=False, two_handed=False):
        self.stat = stat
        self.magic_bonus = magic_bonus
        self.use_mastery = use_mastery
        self.two_handed = two_handed