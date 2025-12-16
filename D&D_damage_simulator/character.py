class Character:
    def __init__(self, lvl, str_mod, dex_mod, cha_mod, wis_mod, con_mod, int_mod):
        self.lvl = lvl
        self.str = str_mod
        self.dex = dex_mod
        self.cha = cha_mod
        self.wis = wis_mod
        self.con = con_mod
        self.int = int_mod

        self.modifiers = []

        self.class_ = None
        self.subclass = None

    def get_stat_mod(self, name):
        return getattr(self, name)

    def get_prof_bonus(self):
        return 2 + (self.lvl - 1) // 4

    def get_modifiers(self):
        return self.modifiers

    def add_modifier(self, modifier_class):
        self.modifiers.append(modifier_class())

    def clear_modifiers(self):
        self.modifiers = []
