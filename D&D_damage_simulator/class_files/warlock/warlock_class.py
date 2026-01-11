from class_files.base_class import BaseClass
from class_files.base_subclass import BaseSubclass
from weapon_files.damage_modifiers import class_features

class Warlock(BaseClass):
    name = "Warlock"

    def get_features(self):
        mods = []

        return mods