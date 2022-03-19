#!/usr/local/bin/env python3

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import socket
import sys
import config
import time
import subprocess
import asyncio
from threading import Thread
import time
from web3 import Web3

upperBoundPercentage = 100
lowerBoundPercentage = 100

performanceRunCounter = 0
performanceRunThreshold = 100

indicatorsCaught = False
tProofGenStarted = None

web3 = Web3(Web3.HTTPProvider(config.URL))
contract_address = web3.toChecksumAddress(config.BOT_CONTRACT_ADDRESS)
BotContract = web3.eth.contract(
    abi=config.BOT_ABI, address=contract_address)


def generate_zkproof(proofType, currentPrice, bollingerBand, percentageBound):
    # go to the proof directory
    subprocess.run(['export', 'PATH=$PATH:/Users/ceren/.zokrates/bin'])
    # compile
    subprocess.run(['cd', '../zokrates-proof/decision-proof'])
    # execute the program
    subprocess.run(['echo', proofType, currentPrice,
                    bollingerBand, percentageBound])
    subprocess.run(['zokrates', 'compute-witness', '-a', proofType,
                    currentPrice, bollingerBand, percentageBound])
    # generate a proof of computation
    subprocess.run(['zokrates', 'generate-proof'])


def get_current_price():
    '''
    const getCurrentPrice = async () => {
        await botContract.methods.getCurrentPrice().send({from: account})
        .on('receipt', function (receipt) {
        // console.log(receipt)
        })
    }
    '''
    BotContract.functions.getCurrentPrice().call({'from': config.ACCOUNT})


def log_loop(tx_hash, x):
    while True:
        try:
            print('Trying to get the transaction receipt')
            tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
            rich_logs = BotContract.events.TestEvent().processReceipt(tx_receipt)
            print(rich_logs)
            print(rich_logs[0]['args'])
            break
        except:
            time.sleep(5)

def trade(num_of_periods, period_length):
    # Get average gas price
    avg_price = web3.eth.generate_gas_price()
    print('Average price is', avg_price, 'wei')

    price = BotContract.functions.getCurrentPrice().call({'from': config.ACCOUNT})
    print('Current price is', price)

    # Fill in your account here
    initial_balance = web3.eth.getBalance(config.ACCOUNT)
    print('Initial balance is', web3.fromWei(
        initial_balance, "ether"), 'ether')

    tx = BotContract.functions.test().buildTransaction({'from': config.ACCOUNT, 'gas': 800000,  'gasPrice': web3.toWei(42, 'gwei'), 'nonce': web3.eth.get_transaction_count(config.ACCOUNT)})
    print(web3.eth.get_transaction_count(config.ACCOUNT))
    print(tx)
    signed_txn = web3.eth.account.sign_transaction(tx, private_key='bc6d600f6bf2a5ad83377dd8743e5fe30b14064ea8e082f3a83ee704cca0cfc0')
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(len(web3.toHex(tx_hash)))
    worker = Thread(target=log_loop, args=(web3.toHex(tx_hash), 5))
    worker.start()
    


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
    trade(10, 10)


if __name__ == '__main__':
    main()
