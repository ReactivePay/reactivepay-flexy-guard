import sys
import logging
import jsonschema as js
from flask import Flask, request, Blueprint, url_for
from flask_restplus import Api, Resource
from flask import jsonify
from functools import wraps
from decimal import Decimal
import json
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime
from rulelookup import RuleLookup
from rulefilter import RuleFilter
import config
import time
import _thread
import storage.rule_model as model
import storage.aggr_model as aggr_model
import storage.aggr as aggr

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger(__name__)
last_update_time = datetime.utcnow()


class Custom_API(Api):
    @property
    def specs_url(self):
        return url_for(self.endpoint('specs'), _external=False)


app = Flask(__name__)
blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Custom_API(blueprint, validate=True, doc='/doc/')
app.register_blueprint(blueprint)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

# JSON schemas

checkRequestSchema = api.schema_model('Check', {
    "type": "object",
    "properties": {
        "data": {
            "type": "string",
            "minLength": 3,
            "maxLength": 1024
        }
    },
    "required": ["data"]
})

getInfoSchema = api.schema_model('Info', {
    "type": "object",
    "properties": {
        "bin": {
            "type": "string",
            "ip": "string",
            "minLength": 6,
            "maxLength": 8
        },
        "ip": {
            "type": "string",
            "ip": "string",
            "minLength": 7,
            "maxLength": 15
        }
    }
})


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        if isinstance(o, Decimal):
            return str(o)
        return json.JSONEncoder.default(self, o)


def validate_schema(schema):
    validator = js.Draft4Validator(schema)

    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            input = request.get_json(force=True)
            errors = [error.message for error in validator.iter_errors(input)]
            if errors:
                response = jsonify(dict(result=False,
                                        message="invalid input",
                                        errors=errors))
                app.logger.info(response)
                response.status_code = 400
                return response
            else:
                return fn(*args, **kwargs)

        return wrapped

    return wrapper


@api.route('/ping')
class Ping(Resource):
    def get(self):
        return {'result': 'true'}

@api.route('/info')
class getInfo(Resource):

    @api.expect(getInfoSchema)
    def post(self):

        req = request.get_json()

        try:
            start_time = time.clock()
            
            res = {}

            if (req['bin']):
                res['bin'] = {}
                country = aggr_model.get_counttries_info(req['bin'], 'bin')
                res['bin'] = country

            if (req['ip']):
                res['ip'] = {}
                country = aggr_model.get_counttries_ip_info(req['ip'], 'ip')
                res['ip'] = country
            
            print("%s, %s" % (time.clock() - start_time, "seconds"))
            res = jsonify({'result': 'OK', 'message': "success", 'data': res})
            res.status_code = 200
        except AssertionError as e:
            print("%s, %s" % (time.clock() - start_time, "seconds"))
            res = jsonify({'result': 'fail', 'message': str(e)})
            res.status_code = 200

        return res

@api.route('/check')
class checkRequest(Resource):

    @api.expect(checkRequestSchema)
    def post(self):

        req = request.get_json()

        try:
            start_time = time.clock()
            print(config.FlexyAggrStorage.key_definitions)

            global last_update_time
            if (model.refresh_rules(last_update_time)):
                print('Reloading rules and definitions ... ')
                config.FlexyAggrStorage = aggr.AggregationStorage()
                config.FlexyRuleStorage.rule_definitions = model.get_rules_dict()
                last_update_time = datetime.utcnow()

            rl = RuleLookup(config.FlexyAggrStorage.key_definitions, req)

            rules = rl.look()
            rf = RuleFilter(rules, req)

            f = rf.filter()

            print("%s, %s" % (time.clock() - start_time, "seconds"))

            res = jsonify({'result': 'OK', 'message': "success", 'data': f})

            res.status_code = 200
        except AssertionError as e:
            print("%s, %s" % (time.clock() - start_time, "seconds"))
            res = jsonify({'result': 'fail', 'message': str(e)})
            res.status_code = 200
        return res

@app.before_request
def log_request_info():
    app.logger.info('Headers: %s', request.headers)
    app.logger.info('Body: %s', request.get_data())
    app.logger.info('Url: %s', request.url)
    app.logger.info('Data: %s', request.data)
    app.logger.info('Args: %s', request.args.__dict__)

if __name__ == '__main__':
    # FlexyAggrStorage = AggregationStorage()
    app.run(host='0.0.0.0',  # os.getenv('SERVER_HOST'),
            port='5000',  # os.getenv('SERVER_PORT'),
            debug=True)  # os.getenv('SERVER_DEBUG'))