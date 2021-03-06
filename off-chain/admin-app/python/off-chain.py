#!/usr/local/bin/env python3

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import socket
import requests
import config
import time
import subprocess
from threading import Thread
import time
import json
import js2py
from hashlib import sha512
from ecdsa import SigningKey, VerifyingKey, NIST384p
from eth_account.messages import defunct_hash_message
from eth_account import Account
from web3 import Web3
from web3.gas_strategies.time_based import fast_gas_price_strategy

upperBoundPercentage = 100
lowerBoundPercentage = 100

performanceRunCounter = 0
performanceRunThreshold = 100

indicatorsCaught = False
tProofGenStarted = None

web3 = Web3(Web3.HTTPProvider(config.URL))
web3.eth.set_gas_price_strategy(fast_gas_price_strategy)
contract_address = web3.toChecksumAddress(config.BOT_CONTRACT_ADDRESS)
BotContract = web3.eth.contract(
    abi=config.BOT_ABI, address=contract_address)

def sign(msg):
    # message = defunct_hash_message(text=msg)
    # signed_message = Account.sign_message(message, private_key=config.STARK_PRIVATE_KEY)
    # print(signed_message)
    
    # js1 = 'console.log( "Hello World!" )'
    # res1 = js2py.eval_js(js1)
    # print(res1)

    # ctx = js2py.EvalJs(enable_require=True)
    # js2py.run_file('./deversifi-webpack/dist/main.js', context=ctx)
    # ctx.execute("esprima.parse('var a = 1')")

    # DVF = require('dvf-client-js') # https://www.npmjs.com/package/random-int
    # ledgerHQ = js2py.require('@ledgerhq/hw-transport-node-hid')

    '''
    For this import to be able to work, you should modify your js2py/node_import.py by adding @ledgerhq/hw-transport-node-hid to line 24:

    + 'cd %s;npm install babel-core babel-cli babel-preset-es2015 babel-polyfill babelify browserify browserify-shim @ledgerhq/hw-transport-node-hid'
    - 'cd %s;npm install babel-core babel-cli babel-preset-es2015 babel-polyfill babelify browserify browserify-shim'

    '''
    # DVF = js2py.require('dvf-client-js/src/dvf')
    # js2py.translate_file('./deversifi-webpack/dist/main.js', 'deversifi.py')

    # import deversifi
    # deversifi.helloWorld()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    params = {
        "body": "{\"cid\":\"long-123\",\"type\":\"EXCHANGE LIMIT\",\"symbol\":\"ETH:USDT\",\"amount\":0.1,\"price\":1000,\"meta\":{\"starkOrder\":{\"vaultIdSell\":1229892728,\"vaultIdBuy\":370326731,\"amountSell\":\"97400000\",\"amountBuy\":\"100000000000000000\",\"tokenSell\":\"0x2\",\"tokenBuy\":\"0x1\",\"nonce\":0,\"expirationTimestamp\":438947},\"starkMessage\":\"597f31e19f2273413833ed1408edd7a2c60e9f82422852a1be7d11049be3268\",\"ethAddress\":\"0x341E46a49F15785373edE443Df0220DEa6a41Bbc\",\"starkPublicKey\":{\"x\":\"00894dc6ae7cb67ba4ee649d3d46afd07c60502fb3477923b1f8185fb02d3580\",\"y\":\"32db0b60b218a8b4b45c2809c3a8e2a1a7ff436d3af889e5ce01046c8fd829a\"},\"starkSignature\":{\"r\":\"5d14357fcf8f489218de0855267c6f64bc463135debf62680ad796e63cd6d3b\",\"s\":\"786ab874d91e3a5871134955fcb768914754760a0ada326af67f758f32819cf\",\"recoveryParam\":0}},\"feeRate\":0.1}",
    }

    url = "https://api.stg.deversifi.com/v1/trading/w/submitOrder"

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=params["body"],
    )

    print(json.dumps(response.json(), indent=2))

    # {"pending":true,"cancelRequested":false,"isPostOnly":false,"isHidden":false,"isFillOrKill":false,"isSlippageDisabled":false,"user":"0x569eced9b05495f8d0766bd3a771f16bdc8b18c3","symbol":"ETH:USDC","amount":-1,"type":"EXCHANGE LIMIT","price":20000000,"feeRate":0.002,"meta":{"ethAddress":"0x569eced9b05495f8d0766bd3a771f16bdc8b18c3","feature":"UNKNOWN","starkPublicKey":{"x":"00894dc6ae7cb67ba4ee649d3d46afd07c60502fb3477923b1f8185fb02d3580","y":"32db0b60b218a8b4b45c2809c3a8e2a1a7ff436d3af889e5ce01046c8fd829a"},"starkOrder":{"vaultIdSell":1229892728,"vaultIdBuy":370326731,"amountSell":"100000000","amountBuy":"19960000000000","tokenSell":"0xb333e3142fe16b78628f19bb15afddaef437e72d6d7f5c6c20c6801a27fba6","tokenBuy":"0x177c7baa25b82a6565927ffd0322b64c672c6b3f79da010a0b798405c66caa6","nonce":765726416,"expirationTimestamp":462094},"starkSignature":{"r":"6db1b9b8bf8a549e65f417c41e3cc6017370d5bce3c00221f871ca32289ef39","s":"3102af84b1eb543172875c0ed27261059d34057d3035147e8ba77577888a91c"},"platform":"DESKTOP","starkMessage":"5e9a10b65c81bde6a983e5eef9ee99826b0d0ffa8b8afe556118217e91dd3e9"},"_id":"Gpkrdbwifgq","tokenBuy":"USDC","tokenSell":"ETH","tokenSellLockedBalance":"100000000","createdAt":"2022-03-22T22:55:20.635Z","updatedAt":"2022-03-22T22:55:20.635Z"}



def generate_zkproof(proof_type, current_price, upper_bollinger_band, lower_bollinger_band, buy_sell_flag, percentage_bound):
    # go to the proof directory
    output = subprocess.run(
        ['export', 'PATH=$PATH:/Users/ceren/.zokrates/bin'], capture_output=True, shell=True)
    print(output)
    # execute the program
    output = subprocess.run(['zokrates', 'compute-witness', '-a', str(current_price), str(upper_bollinger_band), str(
        lower_bollinger_band), str(buy_sell_flag), str(percentage_bound)], capture_output=True, cwd='../../zokrates-proof/decision-proof')
    print(output)
    # generate a proof of computation
    output = subprocess.run(['zokrates', 'generate-proof'], capture_output=True, cwd='../../zokrates-proof/decision-proof')
    print(output)

    # read and return proof
    with open('../../zokrates-proof/decision-proof/proof.json', 'r') as file:
        raw_proof_data = json.load(file)
        print(raw_proof_data)
        return raw_proof_data['proof']['a'], raw_proof_data['proof']['b'], raw_proof_data['proof']['c'], raw_proof_data['inputs']


def deversifi_buy_sell_order(price, amount):
    pass


# const deversifiBuySellOrder = async (price, amount) => {
# if (price==0 || !price){
#     console.log('price is ', price)
#     price = 100000
# }

# // order buy params
# const params = {
# symbol: "ETH:USDC",
# amount: amount,
# price,
# starkPrivateKey
# }

# const dvfConfig = {
# api: 'https://api.stg.deversifi.com',
# wallet: {
#     type: 'tradingKey',
#     meta: {
#     starkPrivateKey
#     }
# }
# }

# const dvf = await DVF(web3, dvfConfig);

# // Buy order placing
# const rOrder = await dvf.submitOrder(params)
# console.info('order receipt', JSON.stringify(rOrder))
# }

def get_current_price():
    BotContract.functions.getCurrentPrice().call({'from': config.ACCOUNT})


def decide_trade(current_price, upper_bollinger_band, lower_bollinger_band):
    print('Deciding on the trade')
    if (current_price > (upper_bollinger_band / 100) * (100 - config.UPPER_BOUND_PERCENTAGE)):
        print("Selling token1")
        a, b, c, inputs = generate_zkproof(
            'sell-proof', current_price, upper_bollinger_band, lower_bollinger_band, 0, config.UPPER_BOUND_PERCENTAGE)
        sign_and_send_tx('trade', {'a': [web3.toInt(hexstr=x) for x in a], 'b': [[web3.toInt(hexstr=x) for x in b[i]] for i in range(
            len(b))], 'c': [web3.toInt(hexstr=x) for x in c], 'inputs': [web3.toInt(hexstr=x) for x in inputs]})
    elif (current_price <= (lower_bollinger_band / 100) * (100 - config.LOWER_BOUND_PERCENTAGE)):
        print("Buying token1")
        a, b, c, inputs = generate_zkproof(
            'buy-proof', current_price, upper_bollinger_band, lower_bollinger_band, 1, config.LOWER_BOUND_PERCENTAGE)
    return a, b, c, inputs


def log_loop(tx_hash, event_name, poll_period):
    while True:
        try:
            print('Trying to get the transaction receipt for', event_name)
            tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
            print('Transaction receipt:', tx_receipt)
            if event_name == 'BollingerIndicators':
                rich_logs = BotContract.events.BollingerIndicators().processReceipt(tx_receipt)
                print('Rich logs for BollingerIndicators: ', rich_logs)
                break
            elif event_name == 'ProofVerified':
                rich_logs = BotContract.events.ProofVerified().processReceipt(tx_receipt)
                print('Rich logs for ProofVerified: ', rich_logs)
                break
        except:
            print('Except')
            time.sleep(poll_period)
    if event_name == 'BollingerIndicators':
        decide_trade(rich_logs[0]['args']['currentPrice'], rich_logs[0]['args']
                     ['upperBollingerBand'], rich_logs[0]['args']['lowerBollingerBand'])


def sign_and_send_tx(tx_name, tx_args):
    event_name = ''
    if tx_name == 'test':
        tx = BotContract.functions.test().buildTransaction(
            {'from': config.ACCOUNT, 'nonce': web3.eth.get_transaction_count(config.ACCOUNT)})
        event_name = 'TestEvent'
    elif tx_name == 'calculateIndicators':
        tx = BotContract.functions.calculateIndicators(tx_args['num_of_periods'], tx_args['period_length']).buildTransaction(
            {'from': config.ACCOUNT, 'nonce': web3.eth.get_transaction_count(config.ACCOUNT)})
        event_name = 'BollingerIndicators'
    elif tx_name == 'trade':
        tx = BotContract.functions.trade(tx_args['a'], tx_args['b'], tx_args['c'], tx_args['inputs']).buildTransaction(
            {'from': config.ACCOUNT, 'nonce': web3.eth.get_transaction_count(config.ACCOUNT)})
        event_name = 'ProofVerified'

    signed_txn = web3.eth.account.sign_transaction(
        tx, private_key=config.ACCOUNT_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    worker = Thread(target=log_loop, args=(
        web3.toHex(tx_hash), event_name, 5))
    worker.start()


def trade(num_of_periods, period_length):
    # Get average gas price
    avg_price = web3.eth.generate_gas_price()
    print('Average price is', avg_price, 'wei')

    price = BotContract.functions.getCurrentPrice().call(
        {'from': config.ACCOUNT})
    print('Current price is', price)

    # Fill in your account here
    initial_balance = web3.eth.getBalance(config.ACCOUNT)
    print('Initial balance is', web3.fromWei(
        initial_balance, "ether"), 'ether')

    # tx = BotContract.functions.test().buildTransaction({'from': config.ACCOUNT, 'gas': 800000,  'gasPrice': web3.toWei(42, 'gwei'), 'nonce': web3.eth.get_transaction_count(config.ACCOUNT)})
    # print(web3.eth.get_transaction_count(config.ACCOUNT))
    # print(tx)
    # signed_txn = web3.eth.account.sign_transaction(tx, private_key='bc6d600f6bf2a5ad83377dd8743e5fe30b14064ea8e082f3a83ee704cca0cfc0')
    # tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    # print(len(web3.toHex(tx_hash)))
    # worker = Thread(target=log_loop, args=(web3.toHex(tx_hash), 5))
    # worker.start()

    sign_and_send_tx('calculateIndicators', {
                     'num_of_periods': num_of_periods, 'period_length': period_length})

    """
    const trade = async (numOfPeriods, periodLength) => {
    // Get average gas price
    // ----------------------
    // web3.eth.getGasPrice().then((result) => {
    //   console.log('price avg: ', web3.utils.fromWei(result, 'gwei'))
    //   })

    // Measure time and gas consumption
    if (performanceRunCounter < 0){
        
        botSocket.once('ProofVerified', {}, (error, event) => {
        if (error) {
            //
        } else {
            tProofVerified = performance.now()
        }
        })
        
        botSocket.once('BollingerIndicators', {}, (error, event) => {
        if (error) {
            //
        } else {
            const currentPrice = event.returnValues.currentPrice
            const upperBollingerBand = event.returnValues.upperBollingerBand
            const lowerBollingerBand = event.returnValues.lowerBollingerBand

            if (currentPrice > (upperBollingerBand / 100) * (100 - upperBoundPercentage)) {
            console.log("Selling token1");
            callProofApi('sell-proof', currentPrice, upperBollingerBand, upperBoundPercentage).then(res => {
                tProofGenEnded = performance.now()
                
                const body = JSON.parse(res)
                botContract.methods.trade(body.a, body.b, body.c, body.inputs, 0).send({from: account, gas: 800000, gasPrice: "10000000000"})
                .on('receipt', function(receipt) {
                // console.log('Trade receipt: ')
                // console.log(receipt)
                var tTradeEnded = performance.now()
                // console.log('tTradeEnded ', tTradeEnded)
                gasUsed += receipt.gasUsed
                web3.eth.getBalance(account).then(res => {
                    var finalBalance = res
                    var deltaBalance = (initialBalance - finalBalance)
                    // console.log("Total WEI used for trading " + deltaBalance)
                    var deltaTotalTime = (tTradeEnded - t0)
                    var deltaTradingTime = (tTradeEnded - tProofGenEnded)
                    var deltaProofGenTime = (tProofGenEnded - tProofGenStarted)
                    var deltaGetIndicators = (tBollingerIndicators - t0)
                    var deltaProofVerifTime = (tProofVerified - tProofGenEnded)
                    // console.log("Trading took " + deltaTotalTime + " milliseconds.")
                    // console.log("Total gas used: ", gasUsed)
                    callPerformanceApi(deltaBalance, deltaGetIndicators, deltaProofGenTime, deltaProofVerifTime , deltaTradingTime, deltaTotalTime, gasUsed).then(()=> {
                    performanceRunCounter += 1
                    trade(numOfPeriods, periodLength)
                    })
                });
                })
            })
            
            //await botContract.methods.trade()
        } else if (currentPrice < (lowerBollingerBand / 100) * (100 + lowerBoundPercentage)) {
            // console.log("Buying token1");
            callProofApi('buy-proof', currentPrice, upperBollingerBand, upperBoundPercentage).then(res => {
                tProofGenEnded = performance.now()
                const body = JSON.parse(res)
                botContract.methods.trade(body.a, body.b, body.c, body.inputs, 1).send({from: account, gas: 800000, gasPrice: "10000000000"})
                .on('receipt', function(receipt) {  
                // console.log('Trade receipt: ')
                // console.log(receipt)
                var tTradeEnded = performance.now()
                gasUsed += receipt.gasUsed
                web3.eth.getBalance(account).then(res => {
                var finalBalance = res
                var deltaBalance = (initialBalance - finalBalance)
                // console.log("Total WEI used for trading " + deltaBalance)
                var deltaTotalTime = (tTradeEnded - t0)
                var deltaTradingTime = (tTradeEnded - tProofGenEnded)
                var deltaProofGenTime = (tProofGenEnded - tProofGenStarted)
                var deltaGetIndicators = (tBollingerIndicators - t0)
                // console.log("Trading took " + deltaTotalTime + " milliseconds.")
                // console.log("Total gas used: ", gasUsed)
                callPerformanceApi(deltaBalance, deltaGetIndicators, deltaProofGenTime, deltaTradingTime, deltaTotalTime, gasUsed).then(()=> {
                    performanceRunCounter += 1
                    trade(numOfPeriods, periodLength)
                })
                });
                
                })
            })
        }
        // else: Hold

        }
        })
    
        await botContract.methods.calculateIndicators(numOfPeriods, periodLength).send({from: account, gas: 800000, gasPrice: "10000000000"})
        .on('receipt', function(receipt) {
        // console.log('calculateIndicators receipt: ')
        // console.log(receipt)
        gasUsed += receipt.gasUsed
        // console.log('gasUsed after calculateIndicators ', gasUsed)
        })
        }
        
    }
    """
    pass


class VsockStream:
    """Client"""

    def __init__(self, conn_tmo=5):
        self.conn_tmo = conn_tmo

    def connect(self, endpoint):
        """Connect to the remote endpoint"""
        self.sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        self.sock.settimeout(self.conn_tmo)
        self.sock.connect(endpoint)

    def send_data(self, data):
        """Send data to a remote endpoint"""
        self.sock.sendall(data)

    def recv_data(self):
        """Receive data from a remote endpoint"""
        while True:
            data = self.sock.recv(1024).decode()
            if not data:
                break
            print(data, end='', flush=True)
        print()

    def disconnect(self):
        """Close the client socket"""
        self.sock.close()


def client_handler(args):
    client = VsockStream()
    endpoint = (args.cid, args.port)
    client.connect(endpoint)
    msg = 'Hello, world!'
    client.send_data(msg.encode())
    client.disconnect()


class VsockListener:
    """Server"""

    def __init__(self, conn_backlog=128):
        self.conn_backlog = conn_backlog

    def bind(self, port):
        """Bind and listen for connections on the specified port"""
        self.sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        self.sock.bind((socket.VMADDR_CID_ANY, port))
        self.sock.listen(self.conn_backlog)

    def recv_data(self):
        """Receive data from a remote endpoint"""
        while True:
            (from_client, (remote_cid, remote_port)) = self.sock.accept()
            # Read 1024 bytes at a time
            while True:
                try:
                    data = from_client.recv(1024).decode()
                except socket.error:
                    break
                if not data:
                    break
                print(data, end='', flush=True)
            print()
            from_client.close()

    def send_data(self, data):
        """Send data to a remote endpoint"""
        while True:
            (to_client, (remote_cid, remote_port)) = self.sock.accept()
            to_client.sendall(data)
            to_client.close()


def server_handler(args):
    server = VsockListener()
    server.bind(args.port)
    server.recv_data()


# def main():
#     parser = argparse.ArgumentParser(prog='vsock-sample')
#     parser.add_argument("--version", action="version",
#                         help="Prints version information.",
#                         version='%(prog)s 0.1.0')
#     subparsers = parser.add_subparsers(title="options")

#     client_parser = subparsers.add_parser("client", description="Client",
#                                           help="Connect to a given cid and port.")
#     client_parser.add_argument("cid", type=int, help="The remote endpoint CID.")
#     client_parser.add_argument("port", type=int, help="The remote endpoint port.")
#     client_parser.set_defaults(func=client_handler)

#     server_parser = subparsers.add_parser("server", description="Server",
#                                           help="Listen on a given port.")
#     server_parser.add_argument("port", type=int, help="The local port to listen on.")
#     server_parser.set_defaults(func=server_handler)

#     if len(sys.argv) < 2:
#         parser.print_usage()
#         sys.exit(1)

#     args = parser.parse_args()
#     args.func(args)


def handle_event(event):
    print('yoyoyoyo')
    print(event)
    # and whatever


# def log_loop(contract, event_filter, poll_interval):
#     while True:
#         print('yeyeyeye')
#         for event in event_filter.get_new_entries():
#             handle_event(event)
#         time.sleep(poll_interval)

#         eventlist = event_filter.get_all_entries()
#         print('eventlist is {}', eventlist)

#         print(contract.events.TestEvent.getLogs(fromBlock='earliest'))


def main():
    # w3 = Web3(Web3.HTTPProvider(
    #     config.URL))
    # contract_address = w3.toChecksumAddress(config.BOT_CONTRACT_ADDRESS)
    # contract = w3.eth.contract(
    #     abi=config.BOT_ABI, address=contract_address)
    # tx_hash = contract.functions.test().transact({'to': contract_address})
    # tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
    # rich_logs = contract.events.TestEvent().processReceipt(tx_receipt)
    # print(rich_logs)
    # print(rich_logs[0]['args'])
    # trade(10, 10)
    print(sign('v2-1647945480.221'))


if __name__ == '__main__':
    main()
