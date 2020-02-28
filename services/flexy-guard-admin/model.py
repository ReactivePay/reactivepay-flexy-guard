
from pymongo import MongoClient
import hashlib
import config as cfg
import json
import datetime

CN = cfg.DB_CONNECTION
client = MongoClient(CN, serverSelectionTimeoutMS=5000000)
db = client['counters']

class RuleListItem():

    Hash = '',
    HashDescr = '',
    Comment = '',
    CreatedAt = ''

class Rule():

    Id = '',
    Hash = '',
    HashDescr = '',
    Header = '',
    Body = '',
    Comment = '',
    CreatedAt = '',
    IsDeleted = False

class Definition():

    Id = '',
    CreatedAt = '',
    Value = '',
    IsDeleted = False

def update_cache(func):
    def wrapper(*args, **kwargs):
        db['refresh'].drop()
        db['refresh'].insert_one({'date': datetime.datetime.utcnow()})
        return func(*args, **kwargs)
    return wrapper

def map_definition(dict):

    de = Definition()
    de.CreatedAt = dict["CreatedAt"]
    de.IsDeleted = dict["IsDeleted"]
    de.Value = dict["Value"]

    return de

def map_rule(dict):

    rule = Rule()
    rule.Id = dict["_id"]
    rule.CreatedAt = dict["CreatedAt"]
    rule.Header = dict["Header"]
    rule.Body = dict["Body"]
    rule.Comment = dict["Comment"]
    rule.Hash = dict["Hash"]
    rule.IsDeleted = dict["IsDeleted"]
    rule.HashDescr = dict["HashDescr"]

    return rule

def map_rulelistitem(dict):

    rule = RuleListItem()
    rule.Hash = dict["Hash"]
    rule.HashDescr = dict["HashDescr"]
    rule.Comment = dict["Comment"]
    rule.CreatedAt = "{:%B %d, %Y}".format(dict["CreatedAt"])

    return rule

def get_rules_collection():
    return db['rules']

def get_def_collection():
    return db['definitions']

def get_ip_country_collection():
    return db['ip:countries']

def get_bin_country_collection():
    return db['bin:countries'] 

def _get_hash(header):
    s_keys_values = []
    for k, v in header.items():
        s_keys_values.append("'%s':'%s'" % (k, v))
    
    hash = hashlib.md5(','.join(s_keys_values).encode()).hexdigest()
    
    return hash

def get_rule_by_hash(hash):

    col = get_rules_collection()
    cur = col.find_one({'Hash': hash, 'IsDeleted': False})
    if cur:
        return map_rule(cur)
    return None

@update_cache
def add_rule(comment, json_string):

    o_json = json.loads(json_string)
    hash = _get_hash(o_json['header'])

    col = get_rules_collection()
    rule = get_rule_by_hash(hash)

    if (rule):
        return {'result': False, 'data': hash}
    
    r = Rule()
    r.CreatedAt = datetime.datetime.utcnow()
    r.Hash = hash
    r.HashDescr = ','.join(["%s:%s" % (k, v) for k, v in o_json['header'].items()])
    r. Header =  o_json['header']
    r.Body = o_json['body']
    r.Comment = comment
    r.IsDeleted = False

    _id = col.insert_one(r.__dict__).inserted_id

    print("Inserted rule: %s" % _id)

    return {'result': True, 'data': hash}

@update_cache
def delete_rule(hash):
    col = get_rules_collection()
    col.update_one({'Hash': hash, 'IsDeleted': False},
                   {'$set': {'IsDeleted': True}})

@update_cache
def update_rule(hash, comment, json_string):
    delete_rule(hash)
    return add_rule(comment, json_string)


def get_rules(text):

    col = get_rules_collection()
    cur = None
    
    if (text or len(text) > 0):
       cur = col.find({'$text': {'$search': text}, 'IsDeleted': False}).sort([('HashDescr', 1)])
    else:
        cur = col.find({'IsDeleted': False}).sort([('HashDescr', 1)])  

    return [map_rulelistitem(cur_item) for cur_item in cur]


def get_definition():
    
    col = get_def_collection()
    cur = col.find_one({'IsDeleted': False})

    if (cur):
        return map_definition(cur)
    else:
        return cur

@update_cache
def add_def(value):

    col = get_def_collection()

    de = Definition()
    de.CreatedAt = datetime.datetime.utcnow()
    de.Value = value
    de.IsDeleted = False

    _id = col.insert_one(de.__dict__).inserted_id

    return get_definition()

@update_cache
def delete_def():
    
    col = get_def_collection()
    col.update_one({'IsDeleted': False}, {'$set': {'IsDeleted': True}})

def update_def(value):

    delete_def()
    return add_def(value)

@update_cache
def update_ip_list(ip_list):

    col = get_ip_country_collection()
    col.delete_many({})
    col.insert_many(ip_list)

@update_cache
def update_bin_list(bin_list):

    col = get_bin_country_collection()
    col.delete_many({})
    col.insert_many(bin_list)

