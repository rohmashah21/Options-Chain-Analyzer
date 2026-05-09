import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# INPUT + DATA FETCH
# =========================
ticker = input("Enter Stock Ticker: ").upper()
stock = yf.Ticker(ticker)

expiries = stock.options

for i, e in enumerate(expiries):
    print(i, e)

expiry = expiries[int(input("Select expiry number: "))]
chain = stock.option_chain(expiry)

# =========================
# CLEAN DATA FUNCTION
# =========================
def clean(df, prefix):
    df = df[["strike", "openInterest", "impliedVolatility", "volume"]]
    df.columns = ["Strike", f"{prefix}_OI", f"{prefix}_IV", f"{prefix}_Vol"]
    return df

calls = clean(chain.calls, "Call")
puts = clean(chain.puts, "Put")

# =========================
# MERGE + FEATURES
# =========================
data = calls.merge(puts, on="Strike")

data["IV"] = (data["Call_IV"] + data["Put_IV"]) / 2
data["Total_OI"] = data["Call_OI"] + data["Put_OI"]
data["Total_Volume"] = data["Call_Vol"] + data["Put_Vol"]

spot = stock.history(period="1d")["Close"].iloc[-1]

# =========================
# PCR + SENTIMENT
# =========================
pcr = data["Put_OI"].sum() / data["Call_OI"].sum()

sentiment = (
    "Bullish" if pcr <= 0.55 else
    "Bearish" if pcr > 1 else
    "Neutral"
)

# =========================
# MAX PAIN (cleaner)
# =========================
strikes = data["Strike"].values
call_oi = data["Call_OI"].values
put_oi = data["Put_OI"].values

losses = []

for i, s in enumerate(strikes):

    call_loss = ((strikes > s) * call_oi * (strikes - s)).sum()
    put_loss  = ((strikes < s) * put_oi * (s - strikes)).sum()

    losses.append(call_loss + put_loss)

data["Loss"] = losses
max_pain = data.loc[data["Loss"].idxmin(), "Strike"]

# =========================
# KEY LEVELS
# =========================
max_call = data.loc[data["Call_OI"].idxmax(), "Strike"]
max_put = data.loc[data["Put_OI"].idxmax(), "Strike"]

# =========================
# TABLE (clean view)
# =========================
print("\nOPTIONS DATA:")
print(data[["Strike","Call_OI","Put_OI","Total_OI","IV"]].to_string(index=False))

# =========================
# TOP LEVELS
# =========================
print("\nTop Call OI:")
print(data.nlargest(5,"Call_OI")[["Strike","Call_OI"]].to_string(index=False))

print("\nTop Put OI:")
print(data.nlargest(5,"Put_OI")[["Strike","Put_OI"]].to_string(index=False))
iv_data = data[data["IV"] > 0]

# =========================
# OUTPUT SUMMARY (compact)
# =========================
print(f"\nSpot: {spot:.2f}")
print(f"PCR: {pcr:.2f} → {sentiment}")
print(f"Max Pain: {max_pain}")
print(f"Resistance: {max_call}")
print(f"Support: {max_put}")

# =========================
# Chart
# =========================

plt.figure(figsize=(10, 5))
plt.plot(iv_data["Strike"], iv_data["IV"], marker="o")

plt.axvline(max_pain, linestyle="--", label="Max Pain")
plt.axvline(spot, linestyle=":", label="Spot Price")

plt.title(f"{ticker} IV Smile")
plt.xlabel("Strike")
plt.ylabel("Implied Volatility")
plt.grid(True)
plt.legend()

plt.show()
plt.figure(figsize=(12, 6))

plt.bar(data["Strike"], data["Call_OI"], alpha=0.6, label="Call OI")
plt.bar(data["Strike"], data["Put_OI"], alpha=0.6, label="Put OI")

plt.axvline(max_pain, linestyle="--", linewidth=2, label="Max Pain")
plt.axvline(spot, linestyle=":", linewidth=2, label="Spot Price")

plt.title(f"{ticker} Open Interest Profile")
plt.xlabel("Strike")
plt.ylabel("Open Interest")
plt.grid(True)
plt.legend()

plt.show()