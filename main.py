"""Dip-buying swing bot for cbBTC (CBBTC/USDC) on the bars-replay/v1 harness.

Strategy, in plain terms: Bitcoin's 1-minute price is noisy, and a full-size
round trip costs about 35 bps in fees, slippage and pool impact, so chasing
every wiggle loses money. This bot waits for a real dip instead: it buys
only when the close sits at least 1.00% below the highest close of the last
480 bars (8 hours), spends 40% of its cash on that first dip, and spends the
rest if the dip deepens to 1.50% below that high. It sells the whole position
when its value reaches 1.50% above its blended cost (fees included) or falls
1.00% below it, then waits 60 bars before it may buy again, so it cannot
re-buy straight into the same falling dip it just stopped out of. A position
that reaches neither exit within 12 hours is sold too, so stale capital is
freed for the next dip.

Everything is integer arithmetic on the raw price units the harness sends
(price_scale 5), so two runs on the same bars produce the same orders byte
for byte. The bot reads no clock, no environment and no network; the only
inputs are the hello message, each batch of bars, and the account the
harness reports. It trades one symbol, CBBTC, long only, and never holds
more than one open position.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# The reference high is the highest close of the last 480 bars (8 hours).
# No signal is taken until 60 closes have been seen, so the high is real.
HIGH_BARS = 480
MIN_HISTORY = 60

# First dip: 1.00% below the 480-bar high, 40% of cash.
DIP1_BPS = 100
TRANCHE1_PCT = 40
# Second dip: 1.50% below the same high, the rest of the cash.
DIP2_BPS = 150
# The second tranche only fires while a meaningful cash pile is still held.
TRANCHE2_MIN_EQUITY_PCT = 5

# Exit when the position is worth 1.50% over its blended cost, or 1.00% under.
EXIT_UP_BPS = 150
EXIT_DOWN_BPS = 100

# Bars to wait after a sell before a new entry may be taken.
COOLDOWN_BARS = 60

# A position that has not reached either exit for 12 hours (720 bars) is sold
# at the next bar, so a stale dip cannot tie the cash up for the rest of the
# window while fresher dips go by. The entry bar is read off the account, not
# off the order that was sent, so a rejected buy cannot start the clock.
MAX_HOLD_BARS = 720

# 1% past the close the order was decided on: a fill further away is refused
# rather than chased, and the bot simply retries on the next bar.
MAX_SLIPPAGE_BPS = 100

BPS = 10_000

# Rolling closes (raw price units), oldest first, at most HIGH_BARS long.
closes = []
# Bars remaining in the post-exit cooldown; 0 means entries are allowed.
cooldown = 0
# Seq of the batch on which the current position first appeared, or None.
entry_seq = None


def _below(close, high, bps):
    """True when close sits at least bps below high, in integers."""
    return close * BPS <= high * (BPS - bps)


def on_batch(state, batch):
    global cooldown, entry_seq
    for bar in batch["bars"]:
        if bar["symbol"] == SYMBOL:
            closes.append(int(bar["c"]))
            if len(closes) > HIGH_BARS:
                del closes[: len(closes) - HIGH_BARS]
    if cooldown > 0:
        cooldown -= 1
    if state.warming_up:
        return []
    close = state.close(SYMBOL)
    if close is None or len(closes) < MIN_HISTORY:
        return []
    high = max(closes)
    held = state.positions.get(SYMBOL)
    min_notional = int(state.hello["fees"]["min_notional_quote_units"])

    if held is None:
        entry_seq = None
        if cooldown > 0:
            return []
        if _below(close, high, DIP1_BPS):
            amount = state.cash * TRANCHE1_PCT // 100
            if amount >= min_notional:
                return [{
                    "side": "buy",
                    "symbol": SYMBOL,
                    "notional_quote_units": amount,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
        return []

    # Holding: exit first, then consider scaling in on a deeper dip.
    if entry_seq is None:
        entry_seq = state.seq
    value = state.value(SYMBOL, held.qty)
    cost = held.cost
    stale = state.seq - entry_seq >= MAX_HOLD_BARS
    if cost > 0:
        if (value * BPS >= cost * (BPS + EXIT_UP_BPS)
                or value * BPS <= cost * (BPS - EXIT_DOWN_BPS)
                or stale):
            cooldown = COOLDOWN_BARS
            entry_seq = None
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
    if state.cash >= max(min_notional, state.equity * TRANCHE2_MIN_EQUITY_PCT // 100):
        if _below(close, high, DIP2_BPS):
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
    return []


makefun_bars.run(on_batch)
