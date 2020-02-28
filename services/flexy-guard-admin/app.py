from flask import Flask, flash, redirect, render_template, request, session, abort
from flask_basicauth import BasicAuth
import model
import json
from dotenv import load_dotenv
import os
import csv

load_dotenv()

app = Flask(__name__, static_url_path='')

app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)

@app.route("/")
def index():
    return render_template('index.html')
    # return "Hello World!"

@app.route("/add", methods=['POST'])
def add():

    res = model.add_rule(request.form["comment"], request.form["rule_json"])
    return render_template('index.html', rule=res)

@app.route("/edit", methods=['GET'])
@app.route("/edit/<hash>", methods=['GET'])
def edit(hash):

    rule = model.get_rule_by_hash(hash)

    res = None

    if rule:
        res = {'Hash': '%s' % rule.Hash, 'HashDescr': rule.HashDescr, 'Comment': rule.Comment,
               'Rule': '%s' % json.dumps({'header': rule.Header, 'body': rule.Body})}

    else:
        abort(404)
        
    return render_template('index.html', edit=res)

@app.route("/update", methods=['POST'])
def update():
    if (request.form["action"] == 'update'):
        res = model.update_rule(request.form["hash"], request.form["comment"], request.form["rule_json"])
        return redirect('/edit/%s' % res['data'], code=302)
    elif (request.form["action"] == 'remove'):
        res = model.delete_rule(request.form["hash"])
        return redirect('/list/', code=302)

@app.route("/list", methods=['GET'])
@app.route("/list/", methods=['GET'])
@app.route("/list/<text>", methods=['GET'])
def rlist(text=''):
    rlist = model.get_rules(text)
    return render_template('rlist.html', rlist=rlist)

@app.route("/search", methods=['POST'])
def search():
    return redirect('/list/%s' % request.form['text'], code=302)

@app.route('/definitions', methods=['GET', 'POST'])
def defintions():
    val = None

    if (request.method == 'GET'):
        de = model.get_definition()
        if (de):
            val = de.Value
    elif (request.method == 'POST'):
        value = request.form["rule_json"]
        de = model.update_def(value)
        val = de.Value
    
    print(val)

    return render_template('definitions.html', definition=val)

def _convert_to_int(val):
    print(val)
    if not isinstance(val, str):
        return ''
    if val.isdigit():
        return int(val)
    else:
        return val

@app.route('/lists', methods=['GET', 'POST'])
def upload_lists():

    if (request.method == 'POST'):
        f = request.files['ip_countries'] 
        if f: 
            fs = f.read().decode('utf-8')
            csv_dicts = [{k: _convert_to_int(v) for k, v in row.items() if k} for row in csv.DictReader(
                    fs.splitlines(), skipinitialspace=True, delimiter=';')]
            model.update_ip_list(csv_dicts)

# need 2 wrap it with a private func
        
        f = request.files['bin_countries']
        if f:
            fs = f.read().decode('utf-8')
            csv_dicts = [{k: _convert_to_int(v) for k, v in row.items() if k} for row in csv.DictReader(
            fs.splitlines(), skipinitialspace=True, delimiter=';')]
            # print(csv_dicts)
            print('Updating mongo')
            model.update_bin_list(csv_dicts)
    
    return render_template('lists.html')


if __name__ == '__main__':
    app.run(host=os.getenv('SERVER_HOST'),
            port=os.getenv('SERVER_PORT'),
            debug=os.getenv('SERVER_DEBUG'))

