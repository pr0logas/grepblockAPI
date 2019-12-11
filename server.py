#!/usr/bin/python3
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask import send_from_directory
from json import dumps
import os
import pymongo

database = 'adeptio'
fromCollection = 'blocks'

mongoAuth = {
    "host" : "127.0.0.1",
    "port" : ":27017",
}

connection = pymongo.MongoClient(mongoAuth['host'] + mongoAuth['port'])
MC = connection[database]

# Flask rules
app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, prefix="/api/v1")
auth = HTTPBasicAuth()


USER_DATA = {
    "admin": "SuperSecretsPwd"
}

@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password

class Blocks(Resource):
    @auth.login_required
    def get(self):
        try:
            searchBlock = MC[fromCollection].find({'block' : 245},{ "_id" : 0})
            return (searchBlock[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')


class Wallets(Resource):
    @auth.login_required
    def get(self):
        try:
            searchWallet = MC['wallets'].find({'block' : 0},{ "_id" : 0})
            return (searchWallet[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

api.add_resource(Blocks, '/block') # Route_1
api.add_resource(Wallets, '/wallet') # Route_1

if __name__ == '__main__':
     app.run()