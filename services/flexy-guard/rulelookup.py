import hashlib
import config


class RuleLookup:

    def __init__(self, keys, data):
        self._keys = keys
        self._data = data

    def _make_key_value(self, k):
        print(k)
        assert k in self._data, "Rule lookup failed, key not found %s" % k
        return "'%s':'%s'" % (k, self._data[k])

    def _makekey(self, key_def):

        key_defs = key_def.split(':')
        assert len(key_defs) > 0, "Rule lookup failed, bad key definition %s" \
            % key_def

        keys_values = [self._make_key_value(k) for k in key_defs]
        # print(keys_values)
        return keys_values

    def _makekeys(self):

        made_keys = \
         [','.join(self._makekey(key_def)) for key_def in self._keys]
        key_hashes = \
            [hashlib.md5(made_key.encode()).hexdigest() for made_key
             in made_keys]

        print("Made keys: %s" % made_keys)
        print("Made hashes: %s" % key_hashes)
        return key_hashes

    def look(self):

        hashes = self._makekeys()
        rules = [config.FlexyRuleStorage.rule_definitions[h]
                 for h in hashes
                 if h in config.FlexyRuleStorage.rule_definitions]

        return rules
