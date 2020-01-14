#!/usr/bin/python3
#:: Author: Tomas Adnriekus
#:: 2019-12-18 - 2020-01-13

import pymongo, json
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address, get_ipaddr
from werkzeug.contrib.fixers import ProxyFix
from flask_restful import Resource, Api
from gevent.pywsgi import WSGIServer
from mongoAuth import auth
from time import gmtime, strftime
import urllib.request
import re

# Init MongoDB
MC = pymongo.MongoClient(auth['host'] + auth['port'])

def get_real_ip():
    print (str(request.remote_addr) + ' Client initiated request ->')
    return (request.remote_addr)

# Flask rules
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)
limiter = Limiter(app, key_func=get_real_ip, default_limits=["6/minute"])
app.url_map.strict_slashes = False
api = Api(app, prefix="/apiv1/free")

notFound = json.loads('{"ERROR" : "No data found"}')

def checkInvalidChars(value):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:,.}{+]')
    if (regex.search(value) == None):
        return 'OK'
    else:
        return 'FAIL'

def webRequest(argument):
    result = notFound
    url = ('https://grepblock.com/parsedb?query='+argument)
    header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) grepblock.com/apiv1/free' }
    req = urllib.request.Request(url, headers=header)

    try:
        response = urllib.request.urlopen(req)
        res = response.read()
        result = res
    except:
        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print(url + timeSet + " FATAL! Error occured!")

    return result

''' http://127.0.0.1:5000/apiv1/free/generalsearch?assetname=all&anyvalue=123 '''
class GlobalSearch(Resource):
    def get(self):
        value = request.args.get('anyvalue')
        blockchain = request.args.get('assetname')
        if blockchain == 'all':
            if checkInvalidChars(value) == 'OK':
                res = webRequest(value)
                # There is NumberLong("21314235345") value in some blockchains, which broke the valid JSON. Try to fix that.
                # Mongo gives us bytes of long string
                try:
                    jsonData = json.loads(res)
                    return jsonData
                except:
                    regex = re.compile(res)
                    qq = (regex.search('NumberLong'))
                    print(qq)

                    if regex.search('NumberLong') == None:
                        print('No NumberLong found')
                    else:
                        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                        numLong = re.search(rb'NumberLong.*?".*?"?"?\)', res)
                        print(numLong)
                        resul = (numLong.group(0))
                        onlyDigits = (re.findall(rb'\d+', resul) [0])
                        final = (str(onlyDigits))
                        aggregate = bytes('"' + final + '"', encoding='utf8')
                        print(aggregate)
                        filedata = res.replace(bytes(resul), bytes(aggregate))
                        jsonData = json.loads(filedata.decode("utf-8"))

                        return jsonData
            else:
                return (json.loads('{"ERROR" : "invalid symbols inside search field"}'))
        else:
            return (json.loads('{"ERROR" : "this method is for global search only"}'))

''' http://127.0.0.1:5000/apiv1/free/getlastblock?assetname=adeptio '''
class GetLastBlock(Resource):
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({},{ "_id": 0, "block": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchLb[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/getlastdifficulty?assetname=adeptio '''
class GetLastDifficulty(Resource):
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchDiff = (MC[blockchain]['blocks'].find({},{ "_id": 0, "difficulty": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchDiff[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/getblockbyhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class GetBlockByHash(Resource):
    def get(self):
        blockH = request.args.get('blockhash')
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({'hash' : str(blockH)},{ "_id" : 0, "block": 1}))
            return (searchLb[0])
        except IndexError:
            return notFound
''' http://127.0.0.1:5000/apiv1/free/getblocktimebynum?assetname=adeptio&num=123 '''
class GetBlockTimeByHeight(Resource):
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
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchWallet = (MC[blockchain]['wallets'].find({},{ "_id": 0}).sort([( '$natural', -1 )] ).limit(1))
            return (searchWallet[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/findbyblocknum?assetname=adeptio&num=123 '''
''' http://127.0.0.1:5000/apiv1/free/findbyblocknum?assetname=all&num=123 '''
class Block(Resource):
    def get(self):
        blockNum = request.args.get('num')
        blockchain = request.args.get('assetname')
        if blockNum.isdigit():
            if blockchain == 'all':
                res = webRequest(blockNum)
                # There is NumberLong("21314235345") value in some blockchains, which broke the valid JSON. Try to fix that.
                # Mongo gives us bytes of long string
                try:
                    jsonData = json.loads(res)
                    return jsonData
                except:
                    timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                    print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                    numLong = re.search(rb'NumberLong.*?".*?"?"?\)', res)
                    resul = (numLong.group(0))
                    onlyDigits = (re.findall(rb'\d+', resul)[0])
                    final = (str(onlyDigits))
                    aggregate = bytes('"' + final + '" }', encoding='utf8')
                    filedata = res.replace(bytes(resul), bytes(aggregate))
                    jsonData = json.loads(filedata)
                    return jsonData
            else:
                try:
                    searchBlock = MC[blockchain]['blocks'].find({'block' : int(blockNum)},{ "_id" : 0})
                    return (searchBlock[0])
                except IndexError:
                    return notFound
        else:
            return (json.loads('{"ERROR" : "num=Only integers are allowed"}'))

''' http://127.0.0.1:5000/apiv1/free/findbyblockhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class Blockhash(Resource):
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
    def get(self):
        walletAddr = request.args.get('addr')
        blockchain = request.args.get('assetname')
        try:
            searchWallet = MC[blockchain]['wallets'].find({'wallet' : walletAddr},{ "_id" : 0})
            return (searchWallet[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5000/apiv1/free/findbyblocknum?assetname=all&num=123 '''

# Routes
api.add_resource(GlobalSearch, '/globalsearch')
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
