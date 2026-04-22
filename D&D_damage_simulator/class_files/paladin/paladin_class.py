from class_files.base_class import BaseClass
from class_files.base_subclass import BaseSubclass
from weapon_files.damage_modifiers import class_features
from utils.attack_count import fighter_modifier

class Paladin(BaseClass):
    name = "Paladin"

    def get_features(self):
        mods = []

        mods.append(class_features.Multiattack)

        return mods

    def get_attack_count(self, weapon) -> int:
        return 2 if weapon.owner.lvl >= 5 else 1