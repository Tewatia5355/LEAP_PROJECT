import os
import binascii
from iroha import IrohaCrypto, primitive_pb2
import commons
from iroha import Iroha, IrohaGrpc
from google.protobuf.timestamp_pb2 import Timestamp
from iroha.primitive_pb2 import can_set_my_account_detail
import sys

if sys.version_info[0] < 3:
    raise Exception('Python 3 or a more recent version is required.')

# Here is the information about the environment and admin account information:
IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')
ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@test')
ADMIN_PRIVATE_KEY = os.getenv(
    'ADMIN_PRIVATE_KEY', 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70')

# Here we will create user keys
user_private_key = IrohaCrypto.private_key()
user_public_key = IrohaCrypto.derive_public_key(user_private_key)
iroha = Iroha(ADMIN_ACCOUNT_ID)
net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT))


def trace(func):
    """
    A decorator for tracing methods' begin/end execution points
    """

    def tracer(*args, **kwargs):
        name = func.__name__
        print('\tEntering "{}"'.format(name))
        result = func(*args, **kwargs)
        print('\tLeaving "{}"'.format(name))
        return result

    return tracer

# Let's start defining the commands:
@trace
def send_transaction_and_print_status(transaction):
    hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    for status in net.tx_status_stream(transaction):
        print(status)

# For example, below we define a transaction made of 2 commands:
# CreateDomain and CreateAsset.
# Each of Iroha commands has its own set of parameters and there are many commands.
# You can check out all of them here:
# https://iroha.readthedocs.io/en/main/develop/api/commands.html
@trace
def create_domain_and_asset():
    """
    Create domain 'domain' and asset 'coin#domain' with precision 2
    """
    commands = [
        iroha.command('CreateDomain', domain_id='domain', default_role='user'),
        iroha.command('CreateAsset', asset_name='leap',
                      domain_id='domain', precision=2)
    ]
# And sign the transaction using the keys from earlier:
    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)
# You can define queries
# (https://iroha.readthedocs.io/en/main/develop/api/queries.html)
# the same way.

@trace
def add_coin_to_admin(amt=1000.00):
    """
    Default -> Add 1000.00 units of 'coin#domain' to 'admin@test'
    """
    amt = str(amt)
    print(amt)
    tx = iroha.transaction([
        iroha.command('AddAssetQuantity',
                      asset_id='coin#domain', amount=amt)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)
    tx_tms = tx.payload.reduced_payload.created_time
    print(tx_tms)
    print("\n\n")
    first_time, last_time = tx_tms - 1, tx_tms + 1
    return first_time, last_time

@trace
def create_account_userone():
    """
    Create account 'customer@domain'
    """
    tx = iroha.transaction([
        iroha.command('CreateAccount', account_name='customer', domain_id='domain',
                      public_key=user_public_key)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def transfer_coin_from_admin_to_userone():
    """
    Transfer 2.00 'coin#domain' from 'admin@test' to 'customer@domain'
    """
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id='customer@domain',
                      asset_id='coin#domain', description='init top up', amount='2.00')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def userone_grants_to_admin_set_account_detail_permission():
    """
    Make 'admin@test' able to set detail to 'customer@domain'
    """
    tx = iroha.transaction([
        iroha.command('GrantPermission', account_id='admin@test',
                      permission=can_set_my_account_detail)
    ], creator_account='customer@domain')
    IrohaCrypto.sign_transaction(tx, user_private_key)
    send_transaction_and_print_status(tx)


@trace
def set_age_to_userone():
    """
    Set age to 'customer@domain' by 'admin@test'
    """
    tx = iroha.transaction([
        iroha.command('SetAccountDetail',
                      account_id='customer@domain', key='age', value='18')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def get_coin_info():
    """
    Get asset info for 'coin#domain'
    :return:
    """
    query = iroha.query('GetAssetInfo', asset_id='coin#domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.asset_response.asset
    print("\n\n")
    print(data)
    print("\n\n")
    print('Asset id = {}, precision = {}'.format(data.asset_id, data.precision))


@trace
def get_account_assets():
    """
    List all the assets of 'customer@domain'
    """
    query = iroha.query('GetAccountAssets', account_id='customer@domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    for asset in data:
        print('Asset id = {}, balance = {}'.format(
            asset.asset_id, asset.balance))
@trace
def get_admin_account_assets():
    """
    List all the assets of 'customer@domain'
    """
    query = iroha.query('GetAccountAssets', account_id='admin@test')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    for asset in data:
        print('Asset id = {}, balance = {}'.format(
            asset.asset_id, asset.balance))

@trace
def query_transactions(first_time = None, last_time = None,
                        first_height = None, last_height = None):
    query = iroha.query('GetAccountTransactions', account_id = ADMIN_ACCOUNT_ID,
                        first_tx_time = first_time,
                        last_tx_time = last_time,
                        first_tx_height = first_height,
                        last_tx_height = last_height,
                        page_size = 3)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)
    response = net.send_query(query)
    return query



@trace
def get_userone_details():
    """
    Get all the kv-storage entries for 'customer@domain'
    """
    query = iroha.query('GetAccountDetail', account_id='customer@domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_detail_response
    print('Account id = {}, details = {}'.format('customer@domain', data.detail))


#######################################################33
@trace
def create_new_account(name):
    test_permissions = [primitive_pb2.can_transfer, primitive_pb2.can_receive, primitive_pb2.can_get_my>
    newUser = commons.new_user(f'{name}@domain')
    genesis_commands = commons.genesis_block({'id':ADMIN_ACCOUNT_ID,'key':ADMIN_PRIVATE_KEY},{'id':f'{n>
    tx = iroha.transaction(genesis_commands)
    IrohaCrypto.sign_transaction(tx,ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def create_account(name):
    """
    Create account 'customer@domain'
    """
    tx = iroha.transaction([
        iroha.command('CreateAccount', account_name=name, domain_id='domain',
                      public_key=user_public_key)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def get_account_details(name):
    query = iroha.query('GetAccountDetail', account_id=f'{name}@domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)
    response = net.send_query(query)
    data = response.account_detail_response
    response = {"Account_Id":f'{name}@domain', "details":data.detail}
    return response

@trace
def get_account_coin_data(name):
    query = iroha.query('GetAccountAssets', account_id=f'{name}@domain')
    IrohaCrypto.sign_query(query,user_private_key)
    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    # for asset in data:
    #     print('Asset id = {}, balance = {}'.format(
    #         asset.asset_id, asset.balance))
    print(len(data))
    print(data)
    if(len(data) > 0):
        return data[0].balance
    return 0

@trace
def transfer_coin(src,dest,amt, desc):
    amt = str(amt)
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id=f'{src}@domain', dest_account_id=f'{dest}@domain',
                      asset_id='coin#domain', description=desc, amount=amt)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def transfer_coin_from_admin(name, amt):
    amt = str(amt)
    print("HERE")
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=f'{name}@domain',
                      asset_id='coin#domain', description='init top up', amount=amt)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def query_transactions_user(first_time = None, last_time = None,
                        first_height = None, last_height = None):
    query = iroha.query('GetAccountTransactions', account_id = ADMIN_ACCOUNT_ID,
                        first_tx_time = first_time,
                        last_tx_time = last_time,
                        first_tx_height = first_height,
                        last_tx_height = last_height,
                        page_size = 3)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)
    response = net.send_query(query)
    return query
