# Hyperliquid Volume Generator

Generate $100k trading volume on Hyperliquid testnet to unlock sub-accounts.

## Quick Start

### 1. Install Dependencies

```bash
cd volume-generator
pip install -r requirements.txt
```

### 2. Configure Your Wallet

```bash
cp .env.example .env
```

Edit `.env` and add your private key:
```
SECRET_KEY=0xYOUR_AGENT_WALLET_PRIVATE_KEY
```

⚠️ **NEVER commit .env!** (It's already in .gitignore)

### 3. Configure Trading Settings

Open `generate_volume.py` and adjust these settings (lines 22-32):

```python
USE_MAINNET = False           # Keep False for testnet
STARTING_VOLUME = 0           # Your current volume
TARGET_VOLUME = 100_000       # Goal: $100k
POSITION_SIZE = 0.03          # 0.03 ETH ≈ $90 per position
COIN = "ETH"                  # Trading pair
LEVERAGE = 10                 # 10x leverage = $900 volume/trade
DELAY_BETWEEN_TRADES = 0.5    # Wait time between trades
```

**Recommended Safe Settings:**
- Position: 0.03 ETH (~$90 at $3k ETH)
- Leverage: 10x (gives $900 volume per open+close cycle)
- Trades needed: ~110 trades to reach $100k

### 4. Run

```bash
python generate_volume.py
```

## How It Works

1. Opens a small position with leverage (buy or sell)
2. Immediately closes the position
3. Repeats until $100k volume reached
4. Each open+close = 2x your position value in volume

**Example:** 0.03 ETH @ $3000 = $90 position × 10x leverage = $900 volume per cycle

## Expected Costs

- **Trading fees**: ~$100-200 for entire $100k volume  
- **Slippage**: Minimal with small positions  
- **Total cost**: ~0.1-0.2% of volume generated  

## Safety

✅ **Locked requirements.txt** - fixed dependencies to reduce attacks  
✅ **Testnet by default** - no real money at risk  
✅ **Small positions** - limits exposure  
✅ **Immediate close** - minimal market risk  
✅ **Progress tracking** - see volume in real-time  

Press `Ctrl+C` to stop anytime.

## Troubleshooting

**"No accountValue" error**: Fund your testnet wallet first  
**Rate limiting**: Increase `DELAY_BETWEEN_TRADES` to 1.0 if needed  
**Trade failures**: Reduce `POSITION_SIZE` or check balance  

## After Completion

Once you hit $100k volume, sub-account features unlock automatically on your Hyperliquid account.
