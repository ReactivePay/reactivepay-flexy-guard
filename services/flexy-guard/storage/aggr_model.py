from pymongo import MongoClient
import storage.config as cfg
import storage.aggr
from enum import Enum
import hashlib
import datetime
from netaddr import IPAddress

CN = cfg.DB_CONNECTION
client = MongoClient(CN)
db = client['counters']


# Operation types
class AggType(Enum):

    Count = "count"
    Sum = "sum"


class AggrCounter():

    Hash = ''
    CreatedAt = ''
    ExpiresAt = ''
    Value = 0
    HashDescriptor = ''

class Definition():

    Id = '',
    CreatedAt = '',
    Value = '',
    IsDeleted = False

def map_definition(dict):

    de = Definition()
    de.CreatedAt = dict["CreatedAt"]
    de.IsDeleted = dict["IsDeleted"]
    de.Value = dict["Value"]

    return de

def get_aggr_by_hash_clause(hash):
    return {"Hash": hash}


def get_aggr_collection(name):
    return db[name]


def get_def_collection():
    return db['definitions']

def get_collection_sum_hash(keys, req, dur):

    key_tail_index = 2
    if dur:
        key_tail_index = 3

    key_values = ["%s:%s" % (k, req[k])
                  for k in keys[:len(keys)-key_tail_index] if k in req]
    key_values.append(keys[len(keys)-2])

    str_to_hash = ','.join(key_values)
    hash = hashlib.md5(str_to_hash.encode()).hexdigest()
    return (str_to_hash, hash)


def get_collection_counter_hash(keys, req, dur=None):

    key_tail_index = 1
    if dur:
        key_tail_index = 2

    key_values = ["%s:%s" % (k, req[k])
                  for k in keys[:len(keys)-key_tail_index] if k in req]

    # key_values.append(keys[len(keys)-2])

    str_to_hash = ','.join(key_values)
    hash = hashlib.md5(str_to_hash.encode()).hexdigest()
    return (str_to_hash, hash)


def map_counter(cur):

    c = AggrCounter()
    c.Hash = cur["Hash"]
    c.CreatedAt = cur["CreatedAt"]
    c.ExpiresAt = cur["ExpiresAt"]
    c.Value = cur["Value"]
    c.HashDescriptor = cur["HashDescriptor"]

    return c


def get_aggr_counter(col, hash):

    cur = col.find_one(get_aggr_by_hash_clause(hash))
    if (cur is not None):
        return map_counter(cur)
    else:
        return cur


# email:amount:sum
def update_sum_counter(col, keys, req, dur=None):

    assert len(keys) > 1, "Can't update aggr counter, keys have invalid len."
    hash_descr = get_collection_sum_hash(keys, req, dur)

    exp_days = 1000
    val_tail_index = 2
    if (dur):
        val_tail_index = 3
        exp_days = int(dur)

    aggr_counter = get_aggr_counter(col, hash_descr[1])

    if (aggr_counter is None):
        aggr_counter = AggrCounter()
        aggr_counter.Hash = hash_descr[1]
        aggr_counter.CreatedAt = datetime.datetime.utcnow()
        aggr_counter.ExpiresAt = datetime.datetime.utcnow() \
            + datetime.timedelta(days=exp_days)
        aggr_counter.Value = req[keys[len(keys)-val_tail_index]]
        aggr_counter.HashDescriptor = hash_descr[0]
        col.insert_one(aggr_counter.__dict__)
    else:
        val = aggr_counter.Value + req[keys[len(keys)-val_tail_index]]
        exp_at = aggr_counter.ExpiresAt

        if datetime.datetime.utcnow() > exp_at:
            val = 0
            exp_at = datetime.datetime.utcnow() \
                + datetime.timedelta(days=exp_days)

        col.update_one({'Hash': hash_descr[1]},
                       {'$set': {'Value': val, 'ExpiresAt': exp_at}})


# email:amount:count
def update_cnt_counter(col, keys, req, dur=None):

    exp_days = 1000
    if (dur):
        exp_days = int(dur)

    assert len(keys) > 1, "Can't update aggr counter, keys have invalid len."
    hash_descr = get_collection_counter_hash(keys, req, dur)

    aggr_counter = get_aggr_counter(col, hash_descr[1])

    if (aggr_counter is None):
        aggr_counter = AggrCounter()
        aggr_counter.Hash = hash_descr[1]
        aggr_counter.CreatedAt = datetime.datetime.utcnow()
        aggr_counter.ExpiresAt = datetime.datetime.utcnow() \
            + datetime.timedelta(days=exp_days)
        aggr_counter.Value = 1
        aggr_counter.HashDescriptor = hash_descr[0]
        col.insert_one(aggr_counter.__dict__)
    else:
        val = aggr_counter.Value + 1
        exp_at = aggr_counter.ExpiresAt
        print(datetime.datetime.utcnow())
        print(exp_at)
        if datetime.datetime.utcnow() > exp_at:
            val = 0
            exp_at = datetime.datetime.utcnow() \
                + datetime.timedelta(days=exp_days)

        col.update_one({'Hash': hash_descr[1]},
                       {'$set': {'Value': val, 'ExpiresAt': exp_at}})


def _update_dur_aggr(aggr_key, req, dur=None):
    key_parts = keys = aggr_key.split(':')
    print(key_parts)

    dur_key = key_parts[len(keys)-1]
    dur_intervals = dur_key[1:][:len(dur_key)-2].split(',')

    for interval in dur_intervals:
        key = ':'.join(key_parts[:len(key_parts)-1]) + ':' + interval
        _update_aggr(key, req, interval)


def _update_aggr(aggr_key, req, dur=None):

    op_tail_index = 1
    if (dur):
        op_tail_index = 2

    col = get_aggr_collection(aggr_key)
    keys = aggr_key.split(':')

    op = keys[len(keys)-op_tail_index]
    print("Updating %s witth op: %s" % (aggr_key, op))

    if (keys[len(keys)-op_tail_index] == storage.aggr.FSD.SUM.value):
        update_sum_counter(col, keys, req, dur)
        return ()

    if (keys[len(keys)-op_tail_index] == storage.aggr.FSD.COUNT.value):
        update_cnt_counter(col, keys, req, dur)


def validate_filter(filter_key, filter_val, req):

    col = get_aggr_collection(filter_key)
    keys = filter_key.split(':')

    hash = None
    req_key = keys[len(keys)-3]
    
    assert keys[len(keys)-3] in req, "No %s key in request" % req_key
    req_val = 0

    if (storage.aggr.FSD.SUM.value in keys):
        hash = get_collection_sum_hash(keys, req, keys[len(keys)-1])
        req_val = req[req_key]

    if (storage.aggr.FSD.COUNT.value in keys):
        hash = get_collection_counter_hash(keys, req, keys[len(keys)-1])
        req_val = 1

    assert hash is not None, "Invalid counter hash: %s" % filter_key

    counter = get_aggr_counter(col, hash[1])

    val = 0

    if (counter is None):
        print( "Counter %s, %s not found" % (filter_key, hash[0]))
    else:
        val = counter.Value

    print("Validating aggr: %s+%s >= %s" % (val, req_val, filter_val[0]))

    assert val + req_val >= filter_val[0], "%s=>%s=>%s" \
        % (filter_key, filter_val[0]+req_val, val)

    print("Validating aggr: %s+%s <= %s" % (val, req_val, filter_val[1]))

    assert val + req_val <= filter_val[1], "%s=>%s=>%s" \
        % (filter_key, filter_val[1], val + req_val)

    _update_aggr(filter_key, req, keys[len(keys)-1])

def get_counttries(val_to_check, key):

    col = db["%s:countries" % key]
    print(col)
    country = col.find_one({'%s' % key: int(val_to_check)})
    assert country is not None, "Country for %s=%s not found" % (key, val_to_check)
    return country["ccode_short"]

def get_counttries_info(val_to_check, key):

    col = db["%s:countries" % key]
    print(col)
    country = col.find_one({'%s' % key: int(val_to_check)})
    assert country is not None, "Country for %s=%s not found" % (key, val_to_check)
    return {
             'ps': country['ps'],
             'bank_name': country['bank_name'],
             'type': country['type'],
             'sub_type': country['sub_type'],
             'country': country['country'],
             'ccode_short': country['ccode_short'],
             'ccode_iso': country['ccode_iso'],
             'code': country['code'],
             'www': country['www']
            }

def get_counttries_ip(val_to_check, key):

    col = db["%s:countries" % key]
    print(col)
    ip = int(IPAddress(val_to_check))
    country = col.find_one({"$and": [{"IP1_int": {"$lt": ip}}, {"IP2_int": {"$gt": ip}}]})

    assert country is not None, "Country for %s=%s not found" % (key, val_to_check)
    return country["code_short"]
    
def get_counttries_ip_info(val_to_check, key):

    col = db["%s:countries" % key]
    print(col)
    ip = int(IPAddress(val_to_check))
    country = col.find_one({"$and": [{"IP1_int": {"$lte": ip}}, {"IP2_int": {"$gte": ip}}]})

    assert country is not None, "Country for %s=%s not found" % (key, val_to_check)
    return {
             'country': country['country_name'],
             'ccode_short': country['code_short'],
             'ccode_iso': country['code_iso'],
           }

def get_definition():
    
    col = get_def_collection()
    cur = col.find_one({'IsDeleted': False})

    if (cur):
        return map_definition(cur)
    else:
        return cur
    