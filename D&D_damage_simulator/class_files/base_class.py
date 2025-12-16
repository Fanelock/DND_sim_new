class BaseClass:
    name = "Base Class"

    def __init__(self, character):
        self.character = character
        self.subclass = None

    def choose_subclass(self, subclass_cls):
        self.subclass = subclass_cls(self.character)
        return self.subclass

    def get_features(self):
        return []