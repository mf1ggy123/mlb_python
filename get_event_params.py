from KalshiClientsBaseV2ApiKey import ExchangeClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

# Set your credentials and API base
prod_key_id = "a1539644-fcd6-411e-ae45-b7ecfbb3ad0c"  # change if needed
prod_private_key = load_private_key_from_file('kalshi-key.key')
prod_api_base = "https://api.elections.kalshi.com/trade-api/v2"

# Initialize the client
exchange_client = ExchangeClient(
    exchange_api_base=prod_api_base,
    key_id=prod_key_id,
    private_key=prod_private_key
)

# Get event parameters for the MLB game
event_ticker = "KXEMMYLIMITEDACTR"
event_params = {'event_ticker': event_ticker}
event_response = exchange_client.get_event(**event_params)

print('Event keys:', event_response.keys())
print('Event object:', event_response['event'])
print('First market in event_response:', event_response['markets'][0])