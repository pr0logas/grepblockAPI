#!/usr/bin/python3
#:: Author: Tomas Adnriekus
#:: 2019-12-18 - 2020-01-15

import pymongo, json
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address, get_ipaddr
from flask_httpauth import HTTPBasicAuth
from werkzeug.contrib.fixers import ProxyFix
from flask_restful import Resource, Api
from gevent.pywsgi import WSGIServer
from mongoAuth import auth
from time import gmtime, strftime
import urllib.request
import re

notFound = json.loads('{"ERROR" : "No data found"}')

# User Database
USER_DATA = {
    "admin": "SuperSecretsPwd312315"
}

# Init MongoDB
MC = pymongo.MongoClient(auth['host'] + auth['port'])

def get_real_ip():
    print (str(request.remote_addr) + ' Client initiated request ->')
    return (request.remote_addr)

# Flask rules
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)
limiter = Limiter(app, key_func=get_real_ip, default_limits=["600/minute"])
app.url_map.strict_slashes = False
api = Api(app, prefix="/apiv1/pro")
auth = HTTPBasicAuth()

@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password

def checkInvalidChars(value):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:,.}{+]')
    if (regex.search(value) == None):
        return 'OK'
    else:
        return 'FAIL'

def webRequest(argument):
    result = notFound
    url = ('https://grepblock.com/parsedb?query='+argument)
    header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) grepblock.com/apiv1/pro' }
    req = urllib.request.Request(url, headers=header)

    try:
        response = urllib.request.urlopen(req)
        res = response.read()
        result = res
    except:
        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print(url + timeSet + " FATAL! Error occured!")

    return result

''' http://127.0.0.1:5002/apiv1/pro/generalsearch?assetname=all&anyvalue=123 '''
class GlobalSearch(Resource):
    @auth.login_required
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
                    workingData = res
                    test = re.search(rb'NumberLong', workingData)

                    while test != None:
                        test = re.search(rb'NumberLong', workingData)

                        if test == None:
                            break

                        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                        numLong = re.search(rb'NumberLong.*?".*?"?"?\)', workingData)
                        resul = (numLong.group(0))
                        onlyDigits = (re.findall(rb'\d+', resul) [0])
                        final = (str(onlyDigits))
                        aggregate = bytes('"' + final + '"', encoding='utf8')
                        workingData = workingData.replace(bytes(resul), bytes(aggregate))

                    fixedJson = json.loads(workingData.decode("utf-8"))
                    return fixedJson
            else:
                return (json.loads('{"ERROR" : "invalid symbols inside search field"}'))
        else:
            return (json.loads('{"ERROR" : "this method is for global search only"}'))

''' http://127.0.0.1:5002/apiv1/pro/getlastblock?assetname=adeptio '''
class GetLastBlock(Resource):
    @auth.login_required
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({},{ "_id": 0, "block": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchLb[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5002/apiv1/pro/getlastdifficulty?assetname=adeptio '''
class GetLastDifficulty(Resource):
    @auth.login_required
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchDiff = (MC[blockchain]['blocks'].find({},{ "_id": 0, "difficulty": 1}).sort([( '$natural', -1 )] ).limit(1))
            return (searchDiff[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5002/apiv1/pro/getblockbyhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class GetBlockByHash(Resource):
    @auth.login_required
    def get(self):
        blockH = request.args.get('blockhash')
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({'hash' : str(blockH)},{ "_id" : 0, "block": 1}))
            return (searchLb[0])
        except IndexError:
            return notFound
''' http://127.0.0.1:5002/apiv1/pro/getblocktimebynum?assetname=adeptio&num=123 '''
class GetBlockTimeByHeight(Resource):
    @auth.login_required
    def get(self):
        block = request.args.get('num')
        blockchain = request.args.get('assetname')
        try:
            searchLb = (MC[blockchain]['blocks'].find({'block' : int(block)},{ "_id" : 0, "time": 1}))
            return (searchLb[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5002/apiv1/pro/getlastparsedwallet?assetname=adeptio '''
class LastParsedWallet(Resource):
    @auth.login_required
    def get(self):
        blockchain = request.args.get('assetname')
        try:
            searchWallet = (MC[blockchain]['wallets'].find({},{ "_id": 0}).sort([( '$natural', -1 )] ).limit(1))
            return (searchWallet[0])
        except IndexError:
            return notFound

''' http://127.0.0.1:5002/apiv1/pro/findbyblocknum?assetname=adeptio&num=123 '''
''' http://127.0.0.1:5002/apiv1/pro/findbyblocknum?assetname=all&num=123 '''
class Block(Resource):
    @auth.login_required
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
                    workingData = res
                    test = re.search(rb'NumberLong', workingData)

                    while test != None:
                        test = re.search(rb'NumberLong', workingData)

                        if test == None:
                            break

                        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                        numLong = re.search(rb'NumberLong.*?".*?"?"?\)', workingData)
                        resul = (numLong.group(0))
                        onlyDigits = (re.findall(rb'\d+', resul) [0])
                        final = (str(onlyDigits))
                        aggregate = bytes('"' + final + '"', encoding='utf8')
                        workingData = workingData.replace(bytes(resul), bytes(aggregate))

                    fixedJson = json.loads(workingData.decode("utf-8"))
                    return fixedJson
            else:
                try:
                    searchBlock = MC[blockchain]['blocks'].find({'block' : int(blockNum)},{ "_id" : 0})
                    return (searchBlock[0])
                except IndexError:
                    return notFound
        else:
            return (json.loads('{"ERROR" : "num=Only integers are allowed"}'))

''' http://127.0.0.1:5002/apiv1/pro/findbyblockhash?assetname=adeptio&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
''' http://127.0.0.1:5002/apiv1/pro/findbyblockhash?assetname=all&blockhash=0000000003115ddfadc6d8b13aff05f0ff76655183a2c3c92a39253bb294f2b9 '''
class Blockhash(Resource):
    @auth.login_required
    def get(self):
        blockHash = request.args.get('blockhash')
        blockchain = request.args.get('assetname')
        if type(blockHash) == str:
            if blockchain == 'all':
                res = webRequest(blockHash)
                # There is NumberLong("21314235345") value in some blockchains, which broke the valid JSON. Try to fix that.
                # Mongo gives us bytes of long string
                try:
                    jsonData = json.loads(res)
                    return jsonData
                except:
                    workingData = res
                    test = re.search(rb'NumberLong', workingData)

                    while test != None:
                        test = re.search(rb'NumberLong', workingData)

                        if test == None:
                            break

                        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                        numLong = re.search(rb'NumberLong.*?".*?"?"?\)', workingData)
                        resul = (numLong.group(0))
                        onlyDigits = (re.findall(rb'\d+', resul) [0])
                        final = (str(onlyDigits))
                        aggregate = bytes('"' + final + '"', encoding='utf8')
                        workingData = workingData.replace(bytes(resul), bytes(aggregate))

                    fixedJson = json.loads(workingData.decode("utf-8"))
                    return fixedJson
            else:
                try:
                    searchBlock = MC[blockchain]['blocks'].find({'hash' : str(blockHash)},{ "_id" : 0})
                    return (searchBlock[0])
                except IndexError:
                    return notFound
        else:
            return (json.loads('{"ERROR" : "hash=Only string are allowed"}'))

''' http://127.0.0.1:5002/apiv1/pro/findbytransaction?assetname=adeptio&txid=238b243ef0063f48c06aa36df5c7861dcf108e870dc468cf7ad7d0f4d9198865 '''
''' http://127.0.0.1:5002/apiv1/pro/findbytransaction?assetname=all&txid=238b243ef0063f48c06aa36df5c7861dcf108e870dc468cf7ad7d0f4d9198865 '''
class Transaction(Resource):
    @auth.login_required
    def get(self):
        transaction = request.args.get('txid')
        blockchain = request.args.get('assetname')
        if type(transaction) == str:
            if blockchain == 'all':
                res = webRequest(transaction)
                # There is NumberLong("21314235345") value in some blockchains, which broke the valid JSON. Try to fix that.
                # Mongo gives us bytes of long string
                try:
                    jsonData = json.loads(res)
                    return jsonData
                except:
                    workingData = res
                    test = re.search(rb'NumberLong', workingData)

                    while test != None:
                        test = re.search(rb'NumberLong', workingData)

                        if test == None:
                            break

                        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                        numLong = re.search(rb'NumberLong.*?".*?"?"?\)', workingData)
                        resul = (numLong.group(0))
                        onlyDigits = (re.findall(rb'\d+', resul) [0])
                        final = (str(onlyDigits))
                        aggregate = bytes('"' + final + '"', encoding='utf8')
                        workingData = workingData.replace(bytes(resul), bytes(aggregate))

                    fixedJson = json.loads(workingData.decode("utf-8"))
                    return fixedJson
            else:
                try:
                    searchBlock = MC[blockchain]['blocks'].find({'tx' : str(transaction)},{ "_id" : 0})
                    return (searchBlock[0])
                except IndexError:
                    return notFound
        else:
            return (json.loads('{"ERROR" : "txid=Only string are allowed"}'))

''' http://127.0.0.1:5002/apiv1/pro/findbywallet?assetname=adeptio&addr=AV12hgJ8VzCt9ANmYCN6rbBLEYPt9VJTP6 '''
''' http://127.0.0.1:5002/apiv1/pro/findbywallet?assetname=all&addr=AV12hgJ8VzCt9ANmYCN6rbBLEYPt9VJTP6 '''
class Wallet(Resource):
    @auth.login_required
    def get(self):
        walletAddr = request.args.get('addr')
        blockchain = request.args.get('assetname')
        if type(transaction) == str:
            if blockchain == 'all':
                res = webRequest(walletAddr)
                # There is NumberLong("21314235345") value in some blockchains, which broke the valid JSON. Try to fix that.
                # Mongo gives us bytes of long string
                try:
                    jsonData = json.loads(res)
                    return jsonData
                except:
                    workingData = res
                    test = re.search(rb'NumberLong', workingData)

                    while test != None:
                        test = re.search(rb'NumberLong', workingData)

                        if test == None:
                            break

                        timeSet = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        print(str(timeSet) + ' ***Failed to return JSON. Probably - "NumberLong" problem. Trying to reformat***')
                        numLong = re.search(rb'NumberLong.*?".*?"?"?\)', workingData)
                        resul = (numLong.group(0))
                        onlyDigits = (re.findall(rb'\d+', resul) [0])
                        final = (str(onlyDigits))
                        aggregate = bytes('"' + final + '"', encoding='utf8')
                        workingData = workingData.replace(bytes(resul), bytes(aggregate))

                    fixedJson = json.loads(workingData.decode("utf-8"))
                    return fixedJson
            else:
                try:
                    searchBlock = MC[blockchain]['wallets'].find({'wallet' : str(walletAddr)},{ "_id" : 0})
                    return (searchBlock[0])
                except IndexError:
                    return notFound
        else:
            return (json.loads('{"ERROR" : "addr=Only string are allowed"}'))

# Routes
#api.add_resource(GlobalSearch, '/globalsearch')
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
    http_server = WSGIServer(('', 5002), app)
    http_server.serve_forever()