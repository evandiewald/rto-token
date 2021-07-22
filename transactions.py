from web3 import Web3, HTTPProvider
import json
import time
import config

w3 = Web3(HTTPProvider(config.INFURA_URL))

contract_abi_json = json.loads(open('contract_abi.json', 'r').read())

contract_address = config.CONTRACT_ADDRESS
rto_contract = w3.eth.contract(address=contract_address, abi=contract_abi_json)


def payRent(landlord, amount_eth):
    txn_dict = rto_contract.functions.payRent(w3.toChecksumAddress(landlord)).buildTransaction({
                'chainId': 3,
                'value': w3.toWei(float(amount_eth), 'ether'),
                'gas': 2000000,
                'gasPrice': w3.toWei('2', 'gwei')
    })
    return txn_dict


def addHome(_listPrice, _renter, _earningsPercent):
    txn_dict = rto_contract.functions.addHome(int(_listPrice), w3.toChecksumAddress(_renter), int(_earningsPercent)).buildTransaction({
        'chainId': 3,
        'value': 0,
        'gas': 2000000,
        'gasPrice': w3.toWei('2', 'gwei')
    })
    return txn_dict


def getHome(_renter):
    home = rto_contract.functions.Homes(w3.toChecksumAddress(_renter)).call()
    return home


def balanceOf(address):
    balance = rto_contract.functions.balanceOf(w3.toChecksumAddress(address)).call()
    return balance


def sign_transaction(txn_dict, wallet_address, private_key):
    txn_dict['nonce'] = w3.eth.getTransactionCount(w3.toChecksumAddress(wallet_address))

    signed_txn = w3.eth.account.signTransaction(txn_dict, private_key=private_key)

    result = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    tx_receipt = None

    count = 0
    while tx_receipt is None and (count < 30):
        try:
            time.sleep(10)

            tx_receipt = w3.eth.getTransactionReceipt(result)

            return tx_receipt
        except:
            tx_receipt = None
            count += 1

    if tx_receipt is None:
        return {'status': 'failed', 'error': 'timeout'}
