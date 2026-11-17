# btc-race-24h-bot

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/lycann666/btc-race-24h-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/lycann666/btc-race-24h-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A dip-buying swing bot that trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute on-chain bars. It waits for a real dip — a close at least 1.00% below the highest close of the last 8 hours — buys 40% of its cash, scales in with the rest if the dip deepens to 1.50%, and sells the whole position at +1.50% over its blended cost or −1.00% under it, with a 60-bar cooldown after every exit and a 12-hour time-stop on stale positions. Pure Python standard library, deterministic integer arithmetic, no network, no clock, no model calls. A full-size round trip costs roughly 35 bps in fees, slippage and pool impact, so the bot only trades when the expected move is clearly larger than that.

Local dev-window grade (kit's frozen 24h window, verified with a faithful replay of the bars-replay/v1 protocol): net PnL **+$27.88** after all fees, **8 trades**, max drawdown **0.72%**, two runs byte-identical.

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
