from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from KalshiClientsBaseV2ApiKey import ExchangeClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import asyncio
import logging

app = FastAPI()
HOME_TEAM = "NON"
AWAY_TEAM = "NON"
EVENT_TICKER = "N/A"
EXCHANGE_CLIENT = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(filename='logfile.log', level=logging.INFO)

ACCEPTED_USERNAMES = {"Michael"}

class LoginRequest(BaseModel):
    username: str

@app.post("/login")
async def login(request: LoginRequest):
    if request.username in ACCEPTED_USERNAMES:
        logging.info(f"User: {request.username}")
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid username")

class TeamSelection(BaseModel):
    home: str
    away: str

@app.post("/select-teams")
async def select_teams(selection: TeamSelection):
    global HOME_TEAM, AWAY_TEAM, EVENT_TICKER, EXCHANGE_CLIENT
    HOME_TEAM = selection.home
    AWAY_TEAM = selection.away
    logging.info(f"Teams selected: Home={HOME_TEAM}, Away={AWAY_TEAM}")
    configureKal()
    set_contracts()
    return {"success": True}

def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def set_contracts():
    global user_contracts, ticker_market, EXCHANGE_CLIENT

    positions_params = {'limit': None,
                        'cursor': None,
                        'settlement_status': None,
                        'ticker': ticker_market["home"],
                        'event_ticker': None}

    current_position = EXCHANGE_CLIENT.get_positions(**positions_params)
    if len(current_position['market_positions']) > 0:
        current_position = current_position['market_positions'][0]['position']
    else:
        current_position = 0
    user_contracts["home"] = current_position

    positions_params = {'limit': None,
                        'cursor': None,
                        'settlement_status': None,
                        'ticker': ticker_market["away"],
                        'event_ticker': None}

    current_position = EXCHANGE_CLIENT.get_positions(**positions_params)
    if len(current_position['market_positions']) > 0:
        current_position = current_position['market_positions'][0]['position']
    else:
        current_position = 0
    user_contracts["away"] = current_position
    print(f"User contracts set: {user_contracts}")


def configureKal():
    global EVENT_TICKER, EXCHANGE_CLIENT, AWAY_TEAM, HOME_TEAM, ticker_market 
    prod_key_id = "a1539644-fcd6-411e-ae45-b7ecfbb3ad0c"  # change if needed
    prod_private_key = load_private_key_from_file('kalshi-key.key')
    prod_api_base = "https://api.elections.kalshi.com/trade-api/v2"
    EXCHANGE_CLIENT = ExchangeClient(
        exchange_api_base=prod_api_base,
        key_id=prod_key_id,
        private_key=prod_private_key
    )
    EVENT_TICKER = makeEventTicker()
    ticker_market["home"] = f"{EVENT_TICKER}-{HOME_TEAM}"
    ticker_market["away"] = f"{EVENT_TICKER}-{AWAY_TEAM}"
    logging.info(f"Configured Kalshi for event: {EVENT_TICKER}", ticker_market["home"],ticker_market["away"])

from datetime import datetime

def get_today_string():
    return datetime.now().strftime("%y%b%d").upper()

def makeEventTicker():
    global HOME_TEAM, AWAY_TEAM
    eventTicker = f"KXMLBGAME-{get_today_string()}{AWAY_TEAM}{HOME_TEAM}"
    logging.info(f"eventTicker: {eventTicker}")
    return eventTicker

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Only send data if teams are selected and EXCHANGE_CLIENT is configured
            if EXCHANGE_CLIENT and EVENT_TICKER != "N/A":
                try:
                    event_params = {'event_ticker': EVENT_TICKER}
                    event_response = EXCHANGE_CLIENT.get_event(**event_params)
                    # Send only the first market's no_bid and yes_bid for simplicity
                    if event_response and "markets" in event_response and len(event_response["markets"]) > 0:
                        market = event_response["markets"]
                        data = {
                            "home" :{
                            "yes_ask": market[0].get("yes_ask"),
                            "yes_bid": market[0].get("yes_bid")
                            },
                            "away" :{
                            "yes_ask": market[1].get("yes_ask"),
                            "yes_bid": market[1].get("yes_bid")
                            }   
                        }
                        await websocket.send_json(data)
                except Exception as e:
                    logging.error(f"Error fetching or sending market data: {e}")
            await asyncio.sleep(2)  # Send update every 2 seconds
    except Exception as e:
        logging.error(f"WebSocket connection closed or error occurred: {e}")
# ...existing imports and code...

# Keep track of contracts for demo purposes
user_contracts = {
    "home": 0,
    "away": 0
}

ticker_market = {
    "home": "",
    "away": ""
}

@app.websocket("/action")
async def websocket_action(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            button = data.get("button")
            contracts = data.get("count")
            print(f"Received action: {data}")
            print(contracts)
            # Button actions
            if button == 1:
                # Buy 1 contract on home team (yes side)
                try:
                    if count > 0:
                        order_params = {
                            "ticker": ticker_market["away"],
                            "client_order_id": "frontend-away-sell",
                            "type": "market",
                            "action": "sell",
                            "side": "yes",
                            "count": count,
                            "yes_price": None,
                            "no_price": None,
                            "expiration_ts": None,
                            "sell_position_floor": None,
                            "buy_max_cost": None
                        }
                        order_result = EXCHANGE_CLIENT.create_order(**order_params)
                        user_contracts["away"] = 0
                        result = {"success": True, "action": "sell_away", "order_result": order_result}
                    else:
                        result = {"success": False, "error": "No away contracts to sell."}
                    order_params = {
                        "ticker": ticker_market["home"],
                        "client_order_id": "frontend-home-buy",
                        "type": "market",
                        "action": "buy",
                        "side": "yes",
                        "count": contracts,
                        "yes_price": None,
                        "no_price": None,
                        "expiration_ts": None,
                        "sell_position_floor": None,
                        "buy_max_cost": None
                    }
                    order_result = EXCHANGE_CLIENT.create_order(**order_params)
                    result = {"success": True, "action": "buy_home", "order_result": order_result}
                    user_contracts["home"] += contracts
                except Exception as e:
                    result = {"success": False, "error": str(e)}
            elif button == 2:
                # Sell all contracts of home team (yes side)
                try:
                    count = user_contracts["home"]
                    if count > 0:
                        order_params = {
                            "ticker": ticker_market["home"],
                            "client_order_id": "frontend-home-sell",
                            "type": "market",
                            "action": "sell",
                            "side": "yes",
                            "count": count,
                            "yes_price": None,
                            "no_price": None,
                            "expiration_ts": None,
                            "sell_position_floor": None,
                            "buy_max_cost": None
                        }
                        order_result = EXCHANGE_CLIENT.create_order(**order_params)
                        user_contracts["home"] = 0
                        result = {"success": True, "action": "sell_home", "order_result": order_result}
                    else:
                        result = {"success": False, "error": "No home contracts to sell."}
                except Exception as e:
                    result = {"success": False, "error": str(e)}
            elif button == 3:
                # Buy 1 contract on away team (yes side)
                try:
                    count = user_contracts["home"]
                    if count > 0:
                        order_params = {
                            "ticker": ticker_market["home"],
                            "client_order_id": "frontend-home-sell",
                            "type": "market",
                            "action": "sell",
                            "side": "yes",
                            "count": count,
                            "yes_price": None,
                            "no_price": None,
                            "expiration_ts": None,
                            "sell_position_floor": None,
                            "buy_max_cost": None
                        }
                        order_result = EXCHANGE_CLIENT.create_order(**order_params)
                        user_contracts["home"] = 0
                        result = {"success": True, "action": "sell_home", "order_result": order_result}
                    else:
                        result = {"success": False, "error": "No home contracts to sell."}
                    order_params = {
                        "ticker": ticker_market["away"],
                        "client_order_id": "frontend-away-buy",
                        "type": "market",
                        "action": "buy",
                        "side": "yes",
                        "count": contracts,
                        "yes_price": None,
                        "no_price": None,
                        "expiration_ts": None,
                        "sell_position_floor": None,
                        "buy_max_cost": None
                    }
                    order_result = EXCHANGE_CLIENT.create_order(**order_params)
                    result = {"success": True, "action": "buy_away", "order_result": order_result}
                    user_contracts["away"] += contracts
                except Exception as e:
                    result = {"success": False, "error": str(e)}
            elif button == 4:
                # Sell all contracts of away team (yes side)
                try:
                    count = user_contracts["away"]
                    if count > 0:
                        order_params = {
                            "ticker": ticker_market["away"],
                            "client_order_id": "frontend-away-sell",
                            "type": "market",
                            "action": "sell",
                            "side": "yes",
                            "count": count,
                            "yes_price": None,
                            "no_price": None,
                            "expiration_ts": None,
                            "sell_position_floor": None,
                            "buy_max_cost": None
                        }
                        order_result = EXCHANGE_CLIENT.create_order(**order_params)
                        user_contracts["away"] = 0
                        result = {"success": True, "action": "sell_away", "order_result": order_result}
                    else:
                        result = {"success": False, "error": "No away contracts to sell."}
                except Exception as e:
                    result = {"success": False, "error": str(e)}
            else:
                result = {"success": False, "error": "Invalid button value."}

            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket /action error: {e}")