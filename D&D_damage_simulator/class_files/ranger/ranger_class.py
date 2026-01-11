from class_files.base_class import BaseClass
from class_files.base_subclass import BaseSubclass
from weapon_files.damage_modifiers import class_features

class Ranger(BaseClass):
    name = "Ranger"

    def get_features(self):
        mods = []

        mods.append(class_features.Multiattack)

        return mods