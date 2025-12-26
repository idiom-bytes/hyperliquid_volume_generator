import os

import eth_account
from dotenv import load_dotenv
from eth_account.signers.local import LocalAccount

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

load_dotenv()


def setup(base_url=None, skip_ws=False):
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise Exception("SECRET_KEY not found in environment. Please set it in your .env file.")

    account: LocalAccount = eth_account.Account.from_key(secret_key)
    print("Running with account address:", account.address)
    
    info = Info(base_url, skip_ws)
    user_state = info.user_state(account.address)
    spot_user_state = info.spot_user_state(account.address)
    margin_summary = user_state["marginSummary"]

    if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
        print("Not running the example because the provided account has no equity.")
        url = info.base_url.split(".", 1)[1]
        error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {account.address} has a balance on {url}.\nIf address shown is your API wallet address, update the config to specify the master address of your account, not the address of the API wallet."
        raise Exception(error_string)

    exchange = Exchange(account, base_url, account_address=account.address)
    return account.address, info, exchange
