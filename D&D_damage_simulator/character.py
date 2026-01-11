from class_files import *

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

        self.default_weapon_name = None
        self.default_weapon_bonus = 0

    def set_class(self, class_cls):
        self.class_ = class_cls(self)

    def set_subclass(self, subclass_cls):
        if not self.class_:
            raise ValueError("Cannot set subclass without a class")
        self.subclass = self.class_.choose_subclass(subclass_cls)

    def apply_class_features(self):
        if self.class_:
            for mod in self.class_.get_features():
                self.add_modifier(mod)

        if self.subclass:
            for mod in self.subclass.get_features():
                self.add_modifier(mod)

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

    def get_default_weapon(self, weapon_mapping):
        name = getattr(self, "default_weapon_name", "")
        if name and name in weapon_mapping:
            return weapon_mapping[name](self)
        return None

    def get_default_weapon_bonus(self):
        return self.default_weapon_bonus