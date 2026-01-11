class BaseSubclass:
    name = "Base Subclass"
    parent_class = None

    def __init__(self, character):
        self.character = character

    def get_features(self):
        return []