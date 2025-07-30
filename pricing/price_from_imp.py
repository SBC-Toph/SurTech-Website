import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---- Parameters ----
input_file = 'abm_market_simulations/abm_market_002.csv' 
strike_price = 0.5                
k = 0.65
# "T = len(df) - 1" df is defined below so it'll have to be parametered there

"""
input_file = CSV of randomly simulated data
strike_price = well... strike price
k = the speed at which an option loses value as time progresses
    0.5 =< k =< 1 : slow decay
    1.5 =< k =< 2.5 : medium decay
    3 =< k =< 5 : Fast decay
T = the total amount of time steps in the DataFrame
"""


# ---- Load CSV ----
df = pd.read_csv(input_file)

T = len(df) - 1
# ---- Calculate Time Decay ---- 
#Needs to better evaluated in the morning seems to not be working right now

df['t_index'] = range(len(df)) # creates a time index for each row

df['decay_multiplier'] = np.exp(-k * (df['t_index'].to_numpy() / T))

df['option_bid_decay'] = df['yes_price'] * (1 - k) *df['decay_multiplier']
df['option_ask_decay'] = (1 - df['no_price']) * (1 - k) * df['decay_multiplier']

print(df['option_bid_decay'])
# ---- Compute option prices ----
# Bid-side: p = yes_price
df['option_bid'] = df['yes_price'] * (1 - strike_price)                         #Verify that time decay is functioning

# Ask-side: p = 1 - no_price
df['option_ask'] = (1 - df['no_price']) * (1 - strike_price) 

# ---- PLOT 1: Dual-Axis Option + Underlying ----
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(df['option_bid_decay'], label='Option Bid Price', marker='o', linestyle='-', color='tab:blue')
ax1.plot(df['option_ask_decay'], label='Option Ask Price', marker='x', linestyle='--', color='tab:orange')
ax1.set_xlabel('Data Point Index')
ax1.set_ylabel('Option Price', color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(True)

ax2 = ax1.twinx()
ax2.plot(df['yes_price'], label='Underlying (Yes Price)', color='tab:green', linestyle=':', linewidth=2)
ax2.set_ylabel('Underlying Value (Yes Price)', color='tab:green')
ax2.tick_params(axis='y', labelcolor='tab:green')

fig.suptitle(f'Option Bid/Ask Prices with Underlying (Dual Axis, Strike = {strike_price})', fontsize=14)
fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
plt.tight_layout()
plt.show()

# ---- PLOT 2: All on Same Axis ----
plt.figure(figsize=(12, 6))
plt.plot(df['option_bid_decay'], label='Bid w/ Time Decay', marker='o', linestyle='-', color='tab:blue')
plt.plot(df['option_ask_decay'], label='Ask w/ Time Decay', marker='x', linestyle='--', color='tab:orange')
plt.plot(df['yes_price'], label='Underlying (Yes Price)', linestyle=':', linewidth=2, color='tab:green')
plt.title(f'Option Prices and Underlying on Same Axis (Strike = {strike_price})')
plt.xlabel('Data Step Index')
plt.ylabel('Option Price')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# ---- OPTIONAL: SAVE TO CSV ----
# df.to_csv('option_prices_output.csv', index=False)
