class AttackContext:

    def __init__(self, stat="str", magic_bonus=0, use_mastery=False, two_handed=False, damage_bonus=0, use_twf=False):
        self.stat = stat
        self.magic_bonus = magic_bonus
        self.use_mastery = use_mastery
        self.two_handed = two_handed
        self.damage_bonus = damage_bonus
        self.use_twf = use_twf  # bare off-hand attack without stat_mod (no TWF fighting style needed)