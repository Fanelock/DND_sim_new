from class_files.base_class import BaseClass
from class_files.base_subclass import BaseSubclass
from weapon_files.damage_modifiers import class_features
from utils.attack_count import eldritch_blast_modifier

class Warlock(BaseClass):
    name = "Warlock"

    def get_features(self):
        mods = []

        return mods

    def get_blast_count(self, weapon) -> int:
        return eldritch_blast_modifier(weapon.owner.lvl)