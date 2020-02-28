from enum import Enum
from storage.aggr import FSD
import storage.aggr_model as st
from config import FlexyAggrStorage as fs


class RuleElements(Enum):

    HEADER = "header"
    BODY = "body"


class RuleFilter():

    def __init__(self, rules, req):
        self._rules = rules
        self._req = req

    def _get_fliler_value(self, body, path):
        keys = path.split(':')
        b = body
        for k in keys:
            b = b[k]
        return b

    def _get_filters(self, path, d, aggr_filters=[],
                     val_filters=[], nic_filters=[],
                     nicip_filters=[], ni_filters=[],
                     in_filters=[], inc_filters=[]):
        for k, v in d.items():
            if isinstance(v, dict):
                self._get_filters(path + ":" + k, v,
                                  aggr_filters=aggr_filters,
                                  val_filters=val_filters,
                                  nic_filters=nic_filters,
                                  nicip_filters=nicip_filters,
                                  ni_filters=ni_filters,
                                  in_filters=in_filters,
                                  inc_filters=inc_filters)
            else:
                val = {"%s:%s" % (path, k): v}

                map_add_filter = {
                    FSD.VALUE.value: val_filters,
                    FSD.NOT_IN_C.value: nic_filters,
                    FSD.IN_C.value: inc_filters,
                    FSD.NOT_IN_IPC.value: nicip_filters,
                    FSD.NOT_IN.value: ni_filters,
                    FSD.IN.value: in_filters

                }
                
                res_filter = aggr_filters
                if (k in map_add_filter):
                    res_filter = map_add_filter[k]

                res_filter.append(val)

    def _check_values(self, val_filters, req):

        for f in val_filters:
            for k, v in f.items():
                keys = k.split(':')
                val_to_check = req[keys[len(keys)-2]]
                assert val_to_check >= v[0], "%s=>%s=>%s" \
                    % (k, v, val_to_check)
                assert val_to_check <= v[1], "%s=>%s=>%s" \
                    % (k, v, val_to_check)

    def _check_aggrs(self, aggr_filters):
        for f in aggr_filters:
            for k, v in f.items():
                fs.check(k, v, self._req)

    def _check_nic(self, nicf, req):
        for f in nicf:
            for k, v in f.items():
                keys = k.split(':')
                key = keys[len(keys)-2]
                val_to_check = req[key]
                c = st.get_counttries(val_to_check, key)
                assert c not in v, "%s=>%s=>%s:%s" \
                    % (k, v, val_to_check, c)

    def _check_inc(self, inc, req):
        for f in inc:
            for k, v in f.items():
                keys = k.split(':')
                key = keys[len(keys)-2]
                val_to_check = req[key]
                c = st.get_counttries(val_to_check, key)
                assert c in v, "%s=>%s=>%s:%s" \
                    % (k, v, val_to_check, c)

    def _check_nicip(self, nicf, req):
        for f in nicf:
            for k, v in f.items():
                keys = k.split(':')
                key = keys[len(keys)-2]
                val_to_check = req[key]
                c = st.get_counttries_ip(val_to_check, key)
                assert c in v, "%s=>%s=>%s" \
                    % (k, v, val_to_check)    

    def _check_ni(self, nif, req):
        for f in nif:
            for k, v in f.items():
                keys = k.split(':')
                key = keys[len(keys)-2]
                val_to_check = req[key]
                assert val_to_check not in v, "%s=>%s=>%s" \
                    % (k, v, val_to_check)

    def _check_in(self, nif, req):
        for f in nif:
            for k, v in f.items():
                keys = k.split(':')
                key = keys[len(keys)-2]
                val_to_check = req[key]
                assert val_to_check in v, "%s=>%s=>%s" \
                    % (k, v, val_to_check)

    def _check(self, rule):

        hb_keys = [k for k in rule.keys()]

        assert len(hb_keys) == 2, "Invalid rule sytax: %s, %s are expected" \
            % (RuleElements.HEADER.value, RuleElements.BODY.value)

        assert hb_keys[1] in rule, "Invalid syntax: %s expected" \
            % (RuleElements.BODY.value)

        body = rule[hb_keys[1]]
        # body_keys = self._get_body_keys(body, key_paths=[])
        # print(body_keys)

        h_prefix = ':'.join(rule[hb_keys[0]].keys())
        af = []
        vf = []
        nicf = []
        nicipf = []
        nif = []
        inf = []
        inc = []

        self._get_filters(h_prefix, body, aggr_filters=af,
                                          val_filters=vf,
                                          nic_filters=nicf,
                                          nicip_filters=nicipf,
                                          ni_filters=nif,
                                          in_filters=inf,
                                          inc_filters = inc)

        print("Aggr filters:")
        print(af)

        print("Val filters:")
        print(vf)

        print("Nicf filters:")
        print(nicf)

        print("NicfIP filters:")
        print(nicipf)

        print("Nif filters:")
        print(nif)

        print("Inf filters:")
        print(inf)

        print("Inc filters:")
        print(inc)
        
        self._check_values(vf, self._req)
        self._check_nic(nicf, self._req)
        self._check_inc(inc, self._req)
        self._check_nicip(nicipf, self._req)
        self._check_ni(nif, self._req)
        self._check_in(inf, self._req)
        self._check_aggrs(af)

        return rule[hb_keys[1]]

    def filter(self):
        return [self._check(rule) for rule in self._rules]
