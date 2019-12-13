#!/usr/bin/python4
import pymongo
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from gevent.pywsgi import WSGIServer
from mongoAuth import auth

# Init MongoDB
MC = pymongo.MongoClient(auth['host'] + auth['port'])

# Flask rules
app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, prefix="/apiv1/free")

''' http://127.0.0.1:5000/apiv1/free/getlastblock?assetname=adeptio '''
class Lastblock(Resource):
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({},{ "_id": 0, "block": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchLb[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

''' http://127.0.0.1:5000/apiv1/free/getdifficulty?assetname=adeptio '''
class Difficulty(Resource):
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({},{ "_id": 0, "difficulty": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchLb[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')


''' http://127.0.0.1:5000/apiv1/free/block?assetname=adeptio&num=123 '''
class Block(Resource):
    def get(self):
        blockNum = request.args.get('num')
        blockchain = request.args.get('assetname')
        try:
            searchBlock = MC[blockchain]['blocks'].find({'block' : int(blockNum)},{ "_id" : 0})
            return (searchBlock[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

''' http://127.0.0.1:5000/apiv1/free/blockhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class Blockhash(Resource):
    def get(self):
        blockHash = request.args.get('blockhash')
        blockchain = request.args.get('assetname')
        try:
            searchBlockhash = MC[blockchain]['blocks'].find({'hash' : str(blockHash)},{ "_id" : 0})
            return (searchBlockhash[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

''' http://127.0.0.1:5000/apiv1/free/transaction?assetname=adeptio&txid=238b243ef0063f48c06aa36df5c7861dcf108e870dc468cf7ad7d0f4d9198865 '''
class Transaction(Resource):
    def get(self):
        transaction = request.args.get('txid')
        blockchain = request.args.get('assetname')
        try:
            searchTxid = MC[blockchain]['blocks'].find({'tx' : transaction},{ "_id" : 0})
            return (searchTxid[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')

''' http://127.0.0.1:5000/apiv1/free/wallet?assetname=adeptio&addr=Aa1Cgn1949UvoZHXRrBVYuihUUL3K6ARPn '''
class Wallet(Resource):
    def get(self):
        walletAddr = request.args.get('addr')
        blockchain = request.args.get('assetname')
        try:
            searchWallet = MC[blockchain]['wallets'].find({'wallet' : walletAddr},{ "_id" : 0})
            return (searchWallet[0])
        except IndexError:
            return ('{"ERROR" : "No data found"}')


api.add_resource(Lastblock, '/getlastblock') 
api.add_resource(Difficulty, '/getdifficulty') 
api.add_resource(Block, '/block') 
api.add_resource(Blockhash, '/blockhash') 
api.add_resource(Transaction, '/transaction') 
api.add_resource(Wallet, '/wallet') 

if __name__ == '__main__':
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()