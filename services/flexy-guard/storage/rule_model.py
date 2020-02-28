from pymongo import MongoClient
import hashlib
import storage.config as cfg
import json
import datetime

CN = cfg.DB_CONNECTION
client = MongoClient(CN)
db = client['counters']

class Rule():

    Hash = '',
    HashDescr = '',
    Header = '',
    Body = '',
    Comment = '',
    CreatedAt = '',
    IsDeleted = False

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

def get_rules_collection():
    return db['rules']

def get_rules_dict():

    col = get_rules_collection()
    cur = col.find({'IsDeleted': False})
    res_dict = {}
    for rule in cur:
        res_dict[rule['Hash']] = {'header': rule['Header'], 'body': rule['Body']}
    
    print(res_dict)
    return res_dict

def to_refresh_rules(val):
    db['refresh'].drop()
    db['refresh'].insert_one({'refresh': val})

def refresh_rules(last_update):
    cur = db['refresh'].find_one()
    if (not cur):
        return False
    elif (cur['date']):
        return cur['date'] > last_update