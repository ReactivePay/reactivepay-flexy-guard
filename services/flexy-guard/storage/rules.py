import json
import storage.rule_model as model
import config

def _loadDefinitions():
    return model.get_rules_dict()


class RuleStorage:

    def __init__(self):
        print("Initializing rules")
        self.rule_definitions  = _loadDefinitions()
