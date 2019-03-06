import os
import argparse
import json
import logging
import traceback

from flask import Flask, redirect, request, jsonify, render_template
from pymongo import MongoClient
from telegram import Bot

dir_path = os.path.dirname(os.path.realpath(__file__))

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
app.secret_key = os.urandom(24)

with open('services.json') as conf_file:
    conf = json.load(conf_file)
    connectionString = conf['mongo']['connectionString']
    telegram_token = conf['telegram']['bot_token']


bot = Bot(telegram_token)

client = MongoClient(connectionString)
db = client.get_default_database()

col_refs = db['referrals']


"""
    render index template
"""
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        return render_template('index.html')
    except Exception as exc:
        print(exc)
        traceback.print_exc()


@app.route('/apply', methods=['POST'])
def register_refferal():
    result = request.form
    full_name = result['ctl00$ContentPlaceHolder1$txtName']
    email = result['ctl00$ContentPlaceHolder1$txtEmailAddress']
    vtx_address = result['ctl00$ContentPlaceHolder1$txtCustomText1']
    try:
        col_refs.insert({"_id": vtx_address, 'email': email, 'full_name': full_name})
        bot.send_message('-295142615',
                         "<b>New Referral</b>\n"
                         "<b>Name</b>: %s\n"
                         "<b>Email</b>: %s\n"
                         "<b>VTXAddress</b>: %s" % (
                             full_name, email, vtx_address),
                         parse_mode='html')
    except Exception as exc:
        print(exc)

    return render_template("response.html", name=full_name)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r



def main():
    parser = argparse.ArgumentParser(description='Beam MimbleWimble')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=2223)
    parser.add_argument('--debug', action='store_true', dest='debug')
    parser.add_argument('--no-debug', action='store_false', dest='debug')
    parser.set_defaults(debug=False)
    args = parser.parse_args()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config["CACHE_TYPE"] = "null"
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
