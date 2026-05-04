import os

import eth_account
from dotenv import load_dotenv
from eth_account.signers.local import LocalAccount

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

# override=False means exported shell vars take precedence over .env
load_dotenv(override=False)


def setup(base_url=None, skip_ws=False, use_target=None):
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise Exception("SECRET_KEY not set. Export it or add it to .env.")

    account: LocalAccount = eth_account.Account.from_key(secret_key)
    print("Agent wallet address:", account.address)

    info = Info(base_url, skip_ws)

    if use_target == "vault":
        address = os.getenv("TARGET_VAULT")
        if not address:
            raise Exception("--target vault requires TARGET_VAULT to be set.")
        print(f"Trading on behalf of vault: {address}")
        exchange = Exchange(account, base_url, vault_address=address)
    elif use_target == "account":
        address = os.getenv("TARGET_ACCOUNT")
        if not address:
            raise Exception("--target account requires TARGET_ACCOUNT to be set.")
        print(f"Trading on behalf of account: {address}")
        # For API-agent authorized accounts, Hyperliquid maps agent→master on the
        # backend. No vault_address in payload — just sign with the agent wallet.
        exchange = Exchange(account, base_url)
    else:
        print("Trading as agent wallet directly.")
        address = account.address
        exchange = Exchange(account, base_url, account_address=address)

    user_state = info.user_state(address)
    spot_user_state = info.spot_user_state(address)
    margin_summary = user_state["marginSummary"]

    if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
        url = info.base_url.split(".", 1)[1]
        raise Exception(
            f"No accountValue: make sure {address} has a balance on {url}."
        )

    return address, info, exchange
