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
    print("Agent wallet address:", account.address)

    target_vault = os.getenv("TARGET_VAULT")
    target_account = os.getenv("TARGET_ACCOUNT")

    if target_vault and target_account:
        raise Exception("Set only one of TARGET_VAULT or TARGET_ACCOUNT, not both.")

    info = Info(base_url, skip_ws)

    if target_vault:
        print(f"Trading on behalf of vault: {target_vault}")
        exchange = Exchange(account, base_url, vault_address=target_vault)
        trading_address = target_vault
    elif target_account:
        print(f"Trading on behalf of account: {target_account}")
        exchange = Exchange(account, base_url, account_address=target_account)
        trading_address = target_account
    else:
        exchange = Exchange(account, base_url, account_address=account.address)
        trading_address = account.address

    user_state = info.user_state(trading_address)
    spot_user_state = info.spot_user_state(trading_address)
    margin_summary = user_state["marginSummary"]

    if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
        print("Not running the example because the target account has no equity.")
        url = info.base_url.split(".", 1)[1]
        error_string = f"No accountValue:\nMake sure that {trading_address} has a balance on {url}."
        raise Exception(error_string)

    return trading_address, info, exchange
