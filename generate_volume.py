"""
Volume Generation Script for Hyperliquid

This script generates trading volume by rapidly opening and closing positions.
Useful for testing multi-sig and sub-account functionality.

Strategy:
- Use high leverage (50x) to maximize volume with minimal capital
- Open small positions and immediately close them
- Track cumulative volume until target is reached
- Minimize risk by using smaller position sizes, lower leverage, and quick execution
"""

import time
import example_utils
from hyperliquid.utils import constants


def main():
    # ==================== CONFIGURATION ====================
    # Network selection
    USE_MAINNET = False  # Set to True for mainnet, False for testnet

    # Volume targets
    STARTING_VOLUME = 0  # Current volume on account (e.g., 30000 if you already have 30k)
    TARGET_VOLUME = 100_000  # $100k USD target volume

    # Trading parameters
    POSITION_SIZE = 0.1  # Small position size in ETH (adjust based on your needs)
    COIN = "ETH"  # Trading pair
    LEVERAGE = 10  # High leverage to maximize volume per trade
    DELAY_BETWEEN_TRADES = 0.25  # Seconds to wait between trades (adjust for rate limits)
    # =======================================================

    # Calculate volume needed
    VOLUME_NEEDED = TARGET_VOLUME - STARTING_VOLUME

    if VOLUME_NEEDED <= 0:
        print("ERROR: Starting volume is already at or above target volume!")
        print(f"Starting Volume: ${STARTING_VOLUME:,}")
        print(f"Target Volume: ${TARGET_VOLUME:,}")
        return

    print("=" * 60)
    print(f"Volume Generation Script - Hyperliquid {'MAINNET' if USE_MAINNET else 'TESTNET'}")
    print("=" * 60)
    print(f"Starting Volume: ${STARTING_VOLUME:,} USD")
    print(f"Target Volume: ${TARGET_VOLUME:,} USD")
    print(f"Volume Needed: ${VOLUME_NEEDED:,} USD")
    print(f"Trading Pair: {COIN}")
    print(f"Position Size: {POSITION_SIZE} {COIN}")
    print(f"Leverage: {LEVERAGE}x")
    print("=" * 60)

    # Setup connection to selected network
    base_url = constants.MAINNET_API_URL if USE_MAINNET else constants.TESTNET_API_URL
    address, info, exchange = example_utils.setup(base_url, skip_ws=True)

    # Get initial account state
    user_state = info.user_state(address)
    margin_summary = user_state["marginSummary"]
    initial_balance = float(margin_summary["accountValue"])

    print(f"\nAccount Address: {address}")
    print(f"Initial Balance: ${initial_balance:.2f}")

    # Set leverage for the trading pair
    print(f"\nSetting leverage to {LEVERAGE}x for {COIN}...")
    leverage_result = exchange.update_leverage(LEVERAGE, COIN)
    print(f"Leverage update result: {leverage_result}")

    # Get current market price to estimate volume per trade
    meta = info.meta()
    coin_meta = next((m for m in meta["universe"] if m["name"] == COIN), None)
    if not coin_meta:
        print(f"Error: Could not find {COIN} in market data")
        return

    # Get orderbook to estimate current price
    l2_data = info.l2_snapshot(COIN)
    if l2_data and "levels" in l2_data and len(l2_data["levels"][0]) > 0:
        mid_price = (float(l2_data["levels"][0][0]["px"]) + float(l2_data["levels"][1][0]["px"])) / 2
    else:
        print("Error: Could not get market price")
        return

    volume_per_trade = POSITION_SIZE * mid_price * 2  # *2 because we open AND close
    estimated_trades = int(VOLUME_NEEDED / volume_per_trade) + 1

    print(f"\nCurrent {COIN} Price: ~${mid_price:.2f}")
    print(f"Volume per trade cycle: ~${volume_per_trade:.2f}")
    print(f"Estimated trades needed: ~{estimated_trades}")
    print(f"\nStarting volume generation...\n")

    # Track statistics (start from STARTING_VOLUME)
    total_volume = STARTING_VOLUME
    session_volume = 0  # Volume generated in this session
    successful_trades = 0
    failed_trades = 0
    start_time = time.time()

    try:
        trade_number = 0
        while session_volume < VOLUME_NEEDED:
            trade_number += 1

            # Alternate between buy and sell to maintain neutral position
            is_buy = (trade_number % 2 == 1)
            action = "BUY" if is_buy else "SELL"

            print(f"[Trade #{trade_number}] {action} {POSITION_SIZE} {COIN}...", end=" ")

            # Open position
            try:
                order_result = exchange.market_open(COIN, is_buy, POSITION_SIZE, None, 0.05)

                if order_result["status"] == "ok":
                    filled_size = 0
                    filled_price = 0

                    for status in order_result["response"]["data"]["statuses"]:
                        if "filled" in status:
                            filled = status["filled"]
                            filled_size = float(filled["totalSz"])
                            filled_price = float(filled["avgPx"])
                            volume = filled_size * filled_price
                            session_volume += volume
                            total_volume += volume
                            print(f"✓ Filled @ ${filled_price:.2f} (Vol: ${volume:.2f})", end=" ")
                        else:
                            print(f"✗ Error: {status.get('error', 'Unknown error')}")
                            failed_trades += 1
                            continue

                    # Brief delay before closing
                    time.sleep(0.1)

                    # Close position
                    print("Closing...", end=" ")
                    close_result = exchange.market_close(COIN)

                    if close_result["status"] == "ok":
                        for status in close_result["response"]["data"]["statuses"]:
                            if "filled" in status:
                                filled = status["filled"]
                                close_size = float(filled["totalSz"])
                                close_price = float(filled["avgPx"])
                                close_volume = close_size * close_price
                                session_volume += close_volume
                                total_volume += close_volume
                                print(f"✓ Closed @ ${close_price:.2f} (Vol: ${close_volume:.2f})")
                                successful_trades += 1
                            else:
                                print(f"✗ Close Error: {status.get('error', 'Unknown error')}")
                                failed_trades += 1
                    else:
                        print(f"✗ Close failed: {close_result}")
                        failed_trades += 1
                else:
                    print(f"✗ Open failed: {order_result}")
                    failed_trades += 1

            except Exception as e:
                print(f"✗ Exception: {str(e)}")
                failed_trades += 1

            # Progress update every 10 trades
            if trade_number % 10 == 0:
                elapsed = time.time() - start_time
                progress = (total_volume / TARGET_VOLUME) * 100
                print(f"\n--- Progress: ${total_volume:,.2f} / ${TARGET_VOLUME:,.2f} ({progress:.1f}%) | Session Vol: ${session_volume:,.2f} | Time: {elapsed:.1f}s ---\n")

            # Rate limiting
            time.sleep(DELAY_BETWEEN_TRADES)

    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")

    # Final statistics
    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    print(f"Starting Volume: ${STARTING_VOLUME:,.2f}")
    print(f"Session Volume Generated: ${session_volume:,.2f}")
    print(f"Total Volume (Current): ${total_volume:,.2f}")
    print(f"Target Volume: ${TARGET_VOLUME:,.2f}")
    print(f"Achievement: {(total_volume/TARGET_VOLUME)*100:.1f}%")
    print(f"Successful Trades: {successful_trades}")
    print(f"Failed Trades: {failed_trades}")
    print(f"Total Time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    if successful_trades > 0:
        print(f"Average Time per Trade: {elapsed_time/successful_trades:.2f} seconds")

    # Get final account state
    user_state = info.user_state(address)
    margin_summary = user_state["marginSummary"]
    final_balance = float(margin_summary["accountValue"])
    pnl = final_balance - initial_balance

    print(f"\nInitial Balance: ${initial_balance:.2f}")
    print(f"Final Balance: ${final_balance:.2f}")
    print(f"PnL: ${pnl:.2f} ({(pnl/initial_balance)*100:.2f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
