import os
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("./stocks_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

API_BASE_URL = "https://www.alphavantage.co"  # Replace with the actual Alpha Vantage API base URL
API_KEY = "0feed937a9mshe685dc54667806ep130cabjsn1845a10af151"  # Replace with your Alpha Vantage API key


def fetch_historical_data(symbol):
    # Fetch historical stock data for t-3 months from the API
    endpoint = f"{API_BASE_URL}/query"
    params = {
        "symbol": symbol,
        "function": "TIME_SERIES_MONTHLY",
        "apikey": API_KEY
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raises an exception for non-200 status codes
        data = response.json()
        time_series_monthly = data.get('Monthly Time Series')

        if time_series_monthly is None:
            print(f"No historical data found for {symbol}.")
            return None

        # Extract date and closing price from the API response
        dates = list(time_series_monthly.keys())
        prices = [float(entry['4. close']) for entry in time_series_monthly.values()]

        return dates, prices
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def generate_chart(symbol):
    data = fetch_historical_data(symbol)
    if data is not None:
        dates, prices = data

        # Determine the color based on price change
        if prices[0] < prices[-1]:
            color = 'g'  # Green for increasing prices
        else:
            color = 'r'  # Red for decreasing prices

        # Create and save the chart with the same filename
        filepath = f"charts/{symbol}_chart.png"
        plt.figure(figsize=(10, 6))
        ax = sns.lineplot(x=dates, y=prices, label=symbol, color=color)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))  # Show major ticks for each month
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))  # Format date as YYYY-MM
        plt.xlabel('Date')
        plt.ylabel('Closing Price')
        plt.title(f"{symbol} Stock Price Chart (T-3 months)")
        plt.xticks(rotation=45)
        plt.legend()
        plt.savefig(filepath)
        plt.close()
        
        return filepath  # Return the filepath for later uploading


def upload_chart(filepath, symbol):
    # Upload the image to Firestore
    with open(filepath, 'rb') as image_file:
        image_data = image_file.read()

    image_ref = db.collection('charts').document(f"{symbol}_chart")
    image_ref.set({'image': image_data})
    print(f"Chart for {symbol} uploaded successfully!")


if __name__ == '__main__':
    symbols = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'FB', 'NVDA', 'JPM', 'JNJ', 'V',
        'PYPL', 'UNH', 'MA', 'BAC', 'ADBE', 'CMCSA', 'XOM', 'INTC', 'VZ', 'NFLX',
        'KO', 'CSCO', 'PEP', 'T', 'CRM', 'PFE', 'DIS', 'ABT', 'ABBV', 'NKE', 'BMY',
        'NVZMY', 'TSM', 'TMUS', 'ACN', 'NVS', 'BABA', 'AMGN', 'ASML', 'AVGO', 'COST',
        'CVX', 'DEO', 'DHR', 'EL', 'NEE', 'PYPL', 'QCOM', 'TM', 'UNP', 'UPS', 'SNY',
        'SAP', 'SBUX', 'NVO', 'MDT', 'LIN', 'LMT', 'LLY', 'HSBC', 'HON', 'GOOG',
        'GL', 'GIS', 'GE', 'FCAU', 'FDX', 'EXC', 'ENB', 'ECL', 'DUK', 'DOV', 'D',
        'COP', 'CCEP', 'CCL', 'BSX', 'BLK', 'BHP', 'BDX', 'AXP', 'APD', 'ANTM',
        'ADI', 'ADP', 'ABEV', 'AAXN', 'AAL', 'A', 'AAP', 'AMD', 'ALB', 'AIV', 'AIG',
        'ABB', 'ABBV', 'ABMD', 'AAPL', 'AMAT', 'APTV', 'ADM', 'ADSK', 'ADP', 'AZO',
    ]

    # Set the default style for seaborn
    sns.set()

    if not os.path.exists('charts'):
        os.makedirs('charts')

    for symbol in symbols:
        filepath = generate_chart(symbol)
        if filepath is not None:
            upload_chart(filepath, symbol)

    print("Chart generation and upload to Firestore complete!")
