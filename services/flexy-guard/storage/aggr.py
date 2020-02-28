from enum import Enum
import json
import storage.aggr_model


class FSD(Enum):
            PARAM = "param"
            NAME = "name"
            AGGR = "aggr"
            TYPE = "type"
            COUNT = "count"
            SUM = "sum"
            DUR = "duration"
            VALUE = "value"
            NOT_IN_C = "not_in_country"
            IN_C = "in_country"
            NOT_IN_IPC = "not_in_ip_country"
            NOT_IN = "not_in"
            IN = "in"


def loadDefinitions():
        de = storage.aggr_model.get_definition()

        
        # assert de is not None, "Aggr definitions not found"
        assert de.Value is not None, "Definition value is empty"

        return json.loads(de.Value)


class AggregationStorage:

    def __init__(self):
        print("Initializing definitions")
        self.aggr_definitions = loadDefinitions()
        print(self.aggr_definitions)
        self.key_definitions = []
        self._aggr_keys = self.build_key_list()

    def _append_key_definition(self, key):

        if (key not in self.key_definitions):
            self.key_definitions.append(key)

    def _get_duration_key_part(self, duration):
        return "[%s]" % ','.join(str(d) for d in duration)

    def _parse_param_key_chain(self, element, key_part):

        print(element)

        if (key_part == ''):
            key_part = element[FSD.NAME.value]
            self._append_key_definition(key_part)

        if (FSD.AGGR.value in element):

            assert FSD.DUR.value in element[FSD.AGGR.value], \
                "%s not found in aggr definition." % FSD.DUR.value

            a_type = element[FSD.AGGR.value][FSD.TYPE.value]

            a_dur = self._get_duration_key_part(
                        element[FSD.AGGR.value][FSD.DUR.value])

            key_part = "%s:%s:%s" % (key_part, a_type, a_dur)

        else:
            next_el = element[FSD.PARAM.value]
            key_part = "%s:%s" % (key_part, next_el[FSD.NAME.value])
            self._append_key_definition(key_part)
            key_part = self._parse_param_key_chain(next_el, key_part)

        return key_part

    def _make_chain(self, path, d, chains=[]):
        if (type(d) is dict):
            name = ''
            for k, v in d.items():
                if (k == FSD.PARAM.value):
                    name = v[FSD.NAME.value]
                    if (path == ''):
                        p = name
                    else:
                        p = "%s:%s" % (path, name)
                    self._append_key_definition(p)
                    self._make_chain(p, v, chains=chains)
                if (k == FSD.AGGR.value):
                    a_type = v[FSD.TYPE.value]
                    a_dur = self._get_duration_key_part(
                        v[FSD.DUR.value])
                    path = "%s:%s:%s" % (path, a_type, a_dur)
                    chains.append(path)

    def build_key_list(self):

        # array_params = [self._parse_param_key_chain(
        #    p[FSD.PARAM.value], '')
        #    for p in self.aggr_definitions]
        array_params = []
        for p in self.aggr_definitions:
            chains = []
            self._make_chain('', p, chains=chains)
            array_params += chains

        print(array_params)
        return array_params

    # def update(self, req):
    #    print('Updating counters ...')
    #    for aggr_key in self._aggr_keys:
    #        storage.aggr_model.update_dur_aggr(aggr_key, req)

    def check(self, filter_key, filter_value, req):
        print('Validating aggregators ... ')
        storage.aggr_model.validate_filter(filter_key, filter_value, req)
