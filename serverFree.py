#!/usr/bin/python4
import pymongo
import json
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Resource, Api
from gevent.pywsgi import WSGIServer
from mongoAuth import auth

# Init MongoDB
MC = pymongo.MongoClient(auth['host'] + auth['port'])

# Flask rules
app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, prefix="/apiv1/free")

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["6/minute"]
    )

notFoundString = json.loads('{"ERROR" : "No data found"}')
notFound = json.dumps(notFoundString)

''' http://127.0.0.1:5000/apiv1/free/getlastblock?assetname=adeptio '''
class GetLastBlock(Resource):
    @limiter.limit("6/minute")
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({},{ "_id": 0, "block": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchLb[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/getlastdifficulty?assetname=adeptio '''
class GetLastDifficulty(Resource):
    @limiter.limit("6/minute")
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchDiff = (MC[blockchain]['blocks'].find({},{ "_id": 0, "difficulty": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchDiff[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/getblockbyhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class GetBlockByHash(Resource):
    @limiter.limit("6/minute")
    def get(self):
        blockH = request.args.get('blockhash')
        print blockH
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({'hash' : str(blockH)},{ "_id" : 0, "block": 1}))
            return (searchLb[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/getblocktimebynum?assetname=adeptio&num=123 '''
class GetBlockTimeByHeight(Resource):
    @limiter.limit("6/minute")
    def get(self):
        block = request.args.get('num')
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({'block' : int(block)},{ "_id" : 0, "time": 1}))
            return (searchLb[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/getlastparsedwallet?assetname=adeptio '''
class LastParsedWallet(Resource):
    @limiter.limit("6/minute")
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchWallet = (MC[blockchain]['wallets'].find({},{ "_id": 0}).sort([( '$natural', -1 )] ).limit(1))
            return (searchWallet[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/findbyblocknum?assetname=adeptio&num=123 '''
class Block(Resource):
    @limiter.limit("6/minute")
    def get(self):
        blockNum = request.args.get('num')
        blockchain = request.args.get('assetname')
        try:
            searchBlock = MC[blockchain]['blocks'].find({'block' : int(blockNum)},{ "_id" : 0})
            return (searchBlock[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/findbyblockhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class Blockhash(Resource):
    @limiter.limit("6/minute")
    def get(self):
        blockHash = request.args.get('blockhash')
        blockchain = request.args.get('assetname')
        try:
            searchBlockhash = MC[blockchain]['blocks'].find({'hash' : str(blockHash)},{ "_id" : 0})
            return (searchBlockhash[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/findbytransaction?assetname=adeptio&txid=238b243ef0063f48c06aa36df5c7861dcf108e870dc468cf7ad7d0f4d9198865 '''
class Transaction(Resource):
    @limiter.limit("6/minute")
    def get(self):
        transaction = request.args.get('txid')
        blockchain = request.args.get('assetname')
        try:
            searchTxid = MC[blockchain]['blocks'].find({'tx' : transaction},{ "_id" : 0})
            return (searchTxid[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/findbywallet?assetname=adeptio&addr=AV12hgJ8VzCt9ANmYCN6rbBLEYPt9VJTP6 '''
class Wallet(Resource):
    @limiter.limit("6/minute")
    def get(self):
        walletAddr = request.args.get('addr')
        blockchain = request.args.get('assetname')
        try:
            searchWallet = MC[blockchain]['wallets'].find({'wallet' : walletAddr},{ "_id" : 0})
            return (searchWallet[0])
        except IndexError:
            return notFound


# Routes
api.add_resource(GetLastBlock, '/getlastblock') 
api.add_resource(GetLastDifficulty, '/getlastdifficulty') 
api.add_resource(LastParsedWallet, '/getlastparsedwallet')
api.add_resource(GetBlockByHash, '/getblockbyhash') 
api.add_resource(GetBlockTimeByHeight, '/getblocktimebynum') 
api.add_resource(Block, '/findbyblocknum') 
api.add_resource(Blockhash, '/findbyblockhash') 
api.add_resource(Transaction, '/findbytransaction') 
api.add_resource(Wallet, '/findbywallet') 

# Serve the high performance http server
if __name__ == '__main__':
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()