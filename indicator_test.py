import json
import pandas as pd
from mplcursors import cursor
import matplotlib.pyplot as plt

from indicators.indicators import *

pd.set_option('display.max_rows', None)

with open('indicators/quotes.json', 'r') as f:
	df = pd.DataFrame(json.loads(f.read()))

df['date'] = pd.to_datetime(df['date'])

df = df.sort_values(by=['date'])
df = df.dropna()
df = df.reset_index(drop=True)

_, df, _ = SimpleMovingAverage(df, period=5, source='close')
df = df.rename(columns={'sma':'sma5'})
_, df, _ = ExponentialMovingAverage(df, period=20, source='close')
df = df.rename(columns={'ema':'ema20'})
_, df, _ = BollingerBands(df, period=20, std='2', source='close')
df = df.rename(columns={'sma':'sma20'})
_, df, _ = Larger(df, 'sma5', 'sma20')
df = df.rename(columns={'larger':'sma5over20'})
_, df, _ = ADXDMI(df)
_, df, _ = PSAR(df)
_, df, _ = HighLow(df, 21, 'close')
_, df, _ = CumulativeReturn(df, 252, 'close')
_, df, _ = RSI(df, 14, 'close')

print(df)

fig = plt.figure(figsize=(19, 10))
ax1 = plt.subplot(2,1,1)
plt.title('SMA, Bollinger, PSAR')

df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

width = 0.9
width2 = 0.1
pricesup = df[df.close >= df.open]
pricesdown = df[df.close < df.open]

ax1.bar(pricesup.index, pricesup.close - pricesup.open, width, bottom=pricesup.open, color='g')
ax1.bar(pricesup.index, pricesup.high - pricesup.close, width2, bottom=pricesup.close, color='g')
ax1.bar(pricesup.index, pricesup.low - pricesup.open, width2, bottom=pricesup.open, color='g')
ax1.bar(pricesdown.index, pricesdown.close - pricesdown.open, width, bottom=pricesdown.open, color='r')
ax1.bar(pricesdown.index, pricesdown.high - pricesdown.open, width2, bottom=pricesdown.open, color='r')
ax1.bar(pricesdown.index, pricesdown.low - pricesdown.close, width2, bottom=pricesdown.close, color='r')

ax1.plot(df['sma5'], label='SMA5')
ax1.plot(df['sma20'], label='SMA20')
ax1.plot(df['ema20'], label='EMA20')
ax1.plot(df['bb_upper'], label='BB', color='gray', linewidth='0.5')
ax1.plot(df['bb_lower'], label='BB', color='gray', linewidth='0.5')
ax1.plot(df['window_high'], label='WindowHigh', color='black', linewidth='0.5')
ax1.plot(df['window_low'], label='WindowLow', color='black', linewidth='0.5')
ax1.scatter(df.index, df['psar'], label='PSAR', color=['green' if item else 'red' for item in df['psar_bull']], s=0.5, marker='o')
ax1.fill_between(df.index, df['bb_lower'], df['bb_upper'], color='skyblue', alpha=0.1)

ax1.legend()
ax1.grid()
ax1.set_xticks(df.index, df['date_str'])
ax1.set_xticks(ax1.get_xticks()[::len(ax1.get_xticks())//12])
cursor(hover=True)

ax2 = plt.subplot(6,1,4, sharex=ax1)
plt.title('Bollinger %B')
ax2.plot(df['bb_pc'], label='BB%B')
ax2.axhline(-3, linestyle='dotted', color='black')
ax2.axhline(-2, linestyle='dotted', color='black')
ax2.axhline(0, linestyle='solid', color='black')
ax2.axhline(2, linestyle='dotted', color='black')
ax2.axhline(3, linestyle='dotted', color='black')
ax2.legend()
ax2.grid()
cursor(hover=True)

ax3 = plt.subplot(6,1,5, sharex=ax1)
plt.title('ADX/DMI')
ax3.plot(df['adx'], label='ADX', color='blue')
ax3.plot(df['dmi_p'], label='DMI+', color='green')
ax3.plot(df['dmi_m'], label='DMI-', color='red')
ax3.axhline(20, linestyle='dotted', color='black')
ax3.legend()
ax3.grid()
cursor(hover=True)

ax3 = plt.subplot(6,1,6, sharex=ax1)
plt.title('RSI')
ax3.plot(df['rsi'], label='RSI')
ax3.axhline(100, linestyle='dotted', color='black')
ax3.axhline(70, linestyle='dotted', color='gray')
ax3.axhline(50, linestyle='solid', color='black')
ax3.axhline(30, linestyle='dotted', color='gray')
ax3.axhline(0, linestyle='dotted', color='black')
ax3.legend()
ax3.grid()
cursor(hover=True)

fig.savefig('indicators/indicators.png', bbox_inches='tight', pad_inches=0)
plt.show()