#!/usr/bin/python3
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask import send_from_directory
from json import dumps
import os
import pymongo

mongoAuth = {
    "host" : "127.0.0.1",
    "port" : ":27017",
}

# Init MongoDB
MC = pymongo.MongoClient(mongoAuth['host'] + mongoAuth['port'])

# Flask rules
app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, prefix="/apiv1/free")


class Blockchain(Resource):
    def get(self):
        blockchain = request.args.get('assetName')
        print(blockchain)
        try:
            searchBlock = MC[fromCollection].find({'block' : 245},{ "_id" : 0})
            return (searchBlock[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

''' http://127.0.0.1:5000/apiv1/free/block?num=123&assetname=adeptio '''
class Blocks(Resource):
    def get(self):
        blockNum = request.args.get('num')
        blockchain = request.args.get('assetname')
        try:
            searchBlock = MC[blockchain]['blocks'].find({'block' : int(blockNum)},{ "_id" : 0})
            return (searchBlock[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

''' /apiv1/free/wallet?addr=Aa1Cgn1949UvoZHXRrBVYuihUUL3K6ARPn&assetname=adeptio '''
class Wallets(Resource):
    def get(self):
        walletAddr = request.args.get('addr')
        blockchain = request.args.get('assetname')
        try:
            searchWallet = MC[blockchain]['wallets'].find({'wallet' : walletAddr},{ "_id" : 0})
            return (searchWallet[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')


api.add_resource(Blocks, '/block') # Route_1
api.add_resource(Wallets, '/wallet') # Route_1

if __name__ == '__main__':
     app.run(port=5000)