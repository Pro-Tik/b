import requests
import time

# Configuration
bot_token = '7526064445:AAGB0pD4QRfI9VIFUZUeaLitFjfBxnglADw'
chat_id = '-1002242797157'  # Group chat ID
coins = ["ARB", "ZK", "MNT", "METIS", "OP", "IMX", "STX", "STRK", 
         "NEXT", "ZRO", "W", "MUBI", "AXL", "ETH", "SOL", 
         "AVAX", "AAVE", "UNI", "PENDLE", "JUP", "JTO", 
         "ENA", "NEAR", "TON", "APT", "FTM"]
base_currency = "USDT"
immediate_alert_threshold = 10  # Percentage change threshold for immediate alerts
investment_advice_threshold = 5  # Percentage change threshold for investment advice
last_message_id = None
last_prices = {}  # To track the last known prices of each coin

# Function to send a message to the group and return the message ID
def send_message(text):
    global last_message_id
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    response = requests.post(url, data=payload)
    
    if response.ok:
        print(f"Send message response: {response.json()}")  # Debugging output
        message_id = response.json().get('result', {}).get('message_id')
        return message_id
    else:
        print(f"Failed to send message: {response.text}")
        return None

# Function to delete the previous message
def delete_message(message_id):
    if message_id:
        url = f'https://api.telegram.org/bot{bot_token}/deleteMessage'
        payload = {'chat_id': chat_id, 'message_id': message_id}
        response = requests.post(url, data=payload)
        if not response.ok:
            print(f"Failed to delete message: {response.text}")

# Function to get the current prices of the specified coins from Binance
def get_binance_data():
    url = 'https://api.binance.com/api/v3/ticker/24hr'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

# Function to filter and retrieve only the relevant coins paired with USDT
def filter_coin_data(data):
    filtered = {item['symbol']: item for item in data if any(coin in item['symbol'] for coin in coins) and base_currency in item['symbol']}
    print(f"Filtered data: {filtered}")  # Debugging output
    return filtered

# Function to check and send an immediate alert if a coin pumps more than 10%
def check_immediate_alert(filtered_data):
    global last_prices

    immediate_alerts = []
    for symbol, coin_info in filtered_data.items():
        current_price = float(coin_info['lastPrice'])
        
        if symbol in last_prices:
            last_price = last_prices[symbol]
            # Check for zero to avoid division by zero
            if last_price == 0:
                print(f"Skipping {symbol} due to last price being zero.")
                continue  # Skip this symbol if last price is zero
            
            price_change = ((current_price - last_price) / last_price) * 100
            
            # Check if price change exceeds the immediate alert threshold
            if price_change >= immediate_alert_threshold:
                immediate_alerts.append(f"{symbol} ✅: +{price_change:.2f}% in the last interval!")
            elif price_change <= -immediate_alert_threshold:
                immediate_alerts.append(f"{symbol} ❌: {price_change:.2f}% in the last interval!")

        # Update the last known price
        last_prices[symbol] = current_price

    # Send immediate alert if there are any qualifying coins
    if immediate_alerts:
        alert_message = "*Immediate Alert: Significant Price Movement Detected!*\n" + "\n".join(immediate_alerts)
        send_message(alert_message)

# Function to generate the report message with current prices and percentage changes
def generate_report(filtered_data):
    gainers = []
    losers = []
    investment_advice = []

    for symbol, coin_info in filtered_data.items():
        current_price = float(coin_info['lastPrice'])
        price_change_percent = float(coin_info['priceChangePercent'])
        
        # Print debugging information
        print(f"Symbol: {symbol}, Last Price: {current_price}, Price Change Percent: {price_change_percent}")

        # Categorize as Gainers or Losers if change is significant
        if price_change_percent > 0:  # Only include gainers
            gainers.append(f"{symbol}: +{price_change_percent:.2f}% ($ {current_price:.2f})\n\n")
            # Suggest for investment if above the investment advice threshold
            if price_change_percent >= investment_advice_threshold:
                investment_advice.append(f"{symbol} is a potential investment! 📈")

        elif price_change_percent < 0:  # Only include losers
            losers.append(f"{symbol}: {price_change_percent:.2f}% ($ {current_price:.2f})\n\n")

    # Create the report message
    report_lines = ["*Binance Market Update*"]
    
    report_lines.append("\n\n*Gainers:*")
    if gainers:
        report_lines.extend(gainers)
    else:
        report_lines.append("None\n\n")
    
    report_lines.append("\n*Losers:*")
    if losers:
        report_lines.extend(losers)
    else:
        report_lines.append("None\n\n")

    report_lines.append("\n*Investment Advice:*")
    if investment_advice:
        report_lines.extend(investment_advice)
    else:
        report_lines.append("No current investment suggestions.\n\n")

    report_lines.append("\n")  # Adding extra space at the end
    return "\n".join(report_lines)

# Main monitoring function
def monitor_binance():
    global last_message_id
    while True:
        try:
            print("Starting Binance market monitoring script...")
            # Fetch Binance market data
            data = get_binance_data()
            filtered_data = filter_coin_data(data)
            print("Data fetched and filtered successfully.")

            # Check for immediate 10% pump alerts
            check_immediate_alert(filtered_data)

            # Generate the report for the 10-minute update
            message = generate_report(filtered_data)
            print(f"Generated report: {message}")  # Debugging output

            # Delete the previous message, if exists
            if last_message_id:
                delete_message(last_message_id)

            # Send the new update and store the message ID
            last_message_id = send_message(message)
            print("Message sent successfully!")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Binance updates: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        # Wait for 10 minutes before the next update
        print("Waiting for 10 minutes before the next update...")
        time.sleep(600)  # Wait for 10 minutes

if __name__ == "__main__":
    monitor_binance()
