from draftkings_mlb_data import fetch_draftkings_mlb_html_data
from getExpectedStats import calculate_expected_margin, read_stats_with_balls_strikes, read_runs_per_inning_balls_strikes_stats, kelly_criterion, dynamic_kelly_fraction, read_leverage_index, build_combined_dict
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import asyncio
from contextlib import asynccontextmanager

from KalshiClientsBaseV2ApiKey import ExchangeClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(odds_polling_task())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
HOME_TEAM = "NON"  # Replace with actual home team
AWAY_TEAM = "NON"  # Replace with actual away team
# Allow frontend to call backend
EVENT_TICKER = "N/A"
EXCHANGE_CLIENT = None
data_dict = build_combined_dict()
balance = 100  # Initial balance
yes_contracts = 0
no_contracts = 0


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(filename='logfile.log', level=logging.INFO)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        logging.info(f"Received: {data}")

        await websocket.send_text(f"Server received: {data}")

async def fetch_betting_odds():
    # Fetch DraftKings MLB HTML data
    global HOME_TEAM, AWAY_TEAM, EXCHANGE_CLIENT, EVENT_TICKER
    if HOME_TEAM == "NON" or AWAY_TEAM == "NON":
        return
    html_data = fetch_draftkings_mlb_html_data(hT=HOME_TEAM, aT=AWAY_TEAM)
    # print("Fetched DraftKings MLB HTML data.")

    # # Example odds and spread (replace with real values from html_data as needed)
    # print(html_data)
    home_spread = html_data["home_team"]["line"]
    away_spread = html_data["away_team"]["line"]
    home_odds = html_data["home_team"]["odds"]
    away_odds = html_data["away_team"]["odds"]

    # Calculate expected margin
    expected_margin = calculate_expected_margin(home_spread, away_spread, home_odds, away_odds)
    # logging.info(f"Expected run margin (away - home): {expected_margin:.2f}")
    # print(f"Expected run margin (away - home): {expected_margin:.2f}")
    # event_params = {'event_ticker': EVENT_TICKER}
    # event_response = EXCHANGE_CLIENT.get_event(**event_params)
    # logging.info(f"event response {event_response}")


async def odds_polling_task():
    print("Starting odds polling task...")
    while True:
        await fetch_betting_odds()
        await asyncio.sleep(7)


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
    global HOME_TEAM, AWAY_TEAM
    HOME_TEAM = selection.home
    AWAY_TEAM = selection.away
    logging.info(f"Teams selected: Home={HOME_TEAM}, Away={AWAY_TEAM}")
    print(f"Received teams: Home={HOME_TEAM}, Away={AWAY_TEAM}")
    configureKal()
    return {"success": True}

def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def configureKal():
    global EVENT_TICKER, EXCHANGE_CLIENT
    prod_key_id = "a1539644-fcd6-411e-ae45-b7ecfbb3ad0c"  # change if needed
    prod_private_key = load_private_key_from_file('kalshi-key.key')
    prod_api_base = "https://api.elections.kalshi.com/trade-api/v2"
    EXCHANGE_CLIENT = ExchangeClient(
    exchange_api_base=prod_api_base,
    key_id=prod_key_id,
    private_key=prod_private_key
    )
    EVENT_TICKER = makeEventTicker()
    print(EVENT_TICKER)
    event_params = {'event_ticker': EVENT_TICKER}
    event_response = EXCHANGE_CLIENT.get_event(**event_params)
    logging.info(f"event response {event_response}")


from datetime import datetime

def get_today_string():
    return datetime.now().strftime("%y%b%d").lower()

def makeEventTicker():
    global HOME_TEAM, AWAY_TEAM
    eventTicker = "KXMLBGAME-"+get_today_string()+AWAY_TEAM+HOME_TEAM
    eventTicker = eventTicker.upper()
    logging.info(f"eventTicker:  {eventTicker}")
    return eventTicker

@app.websocket("/game-state")
async def game_state_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received game state: {data}")
            print(type(data))
            # Optionally, process or store the game state here
            x(data)
            await websocket.send_text("Game state received")
    except Exception as e:
        logging.error(f"WebSocket connection closed or error occurred: {e}")

def x(gamestate):
        global data_dict, balance, EVENT_TICKER, EXCHANGE_CLIENT, yes_contracts, no_contracts
        try:
            print(f"Received game state: {gamestate}")
            event_params = {'event_ticker': EVENT_TICKER}
            gamestate = json.loads(gamestate)
            
            if gamestate['isTop']:
                gamestate["home_away"] = 0
            else:
                gamestate["home_away"] = 1
            winPer, leverage, expected_runs = data_dict[gamestate['inning']][gamestate['home_away']][gamestate['outs']][
        (gamestate['bases'][1], gamestate['bases'][2], gamestate['bases'][3])
    ][gamestate['homeScores'] - gamestate['awayScores']][
        (gamestate['balls'], gamestate['strikes'])
    ]
            event_response = EXCHANGE_CLIENT.get_event(**event_params)
            if winPer is None:
                logging.info('No data available for the current game state.')
                return
            kalshi_home_win = (event_response['markets'][0]['yes_ask'] + (event_response['markets'][0]['yes_ask'] - event_response['markets'][0]['yes_bid']) + 4)/100
            if winPer > kalshi_home_win:
                contracts,_ = kelly_criterion(winPer, event_response['markets'][0]['yes_ask']+0.02, balance, dynamic_kelly_fraction(winPer, gamestate['inning'], leverage, .25))
                contracts = round(contracts/(event_response['markets'][0]['yes_ask']/100+0.02))
                balance -= contracts * (event_response['markets'][0]['yes_ask']/100+0.02)
                if balance < 0:
                    logging.error("Insufficient balance for betting.")
                    balance += contracts * (event_response['markets'][0]['yes_ask']/100+0.02)
                logging.info(f"Balance after home bet: {balance} for {contracts} contracts at {event_response['markets'][0]['yes_ask']}")
                yes_contracts += contracts
            elif yes_contracts > 0 and winPer < event_response['markets'][0]['yes_bid']/100:
                contracts = yes_contracts
                balance += contracts * (event_response['markets'][0]['yes_bid']/100)
                logging.info(f"Balance after home bet sell: {balance} for {contracts} contracts at {event_response['markets'][0]['yes_bid']}")
                yes_contracts = 0

            kalshi_home_lose = (event_response['markets'][0]['no_ask'] + (event_response['markets'][0]['no_ask'] - event_response['markets'][0]['no_bid']) + 4)/100

            if 1-winPer < kalshi_home_lose:
                contracts,_ = kelly_criterion(1-winPer, event_response['markets'][0]['no_ask']+0.02, balance, dynamic_kelly_fraction(1-winPer, gamestate['inning'], leverage, .25))
                contracts = round(contracts/(event_response['markets'][0]['no_ask']/100+0.02))
                balance -= contracts * (event_response['markets'][0]['no_ask']/100+0.02)
                if balance < 0:
                    logging.error("Insufficient balance for betting.")
                    balance += contracts * (event_response['markets'][0]['yes_ask']/100+0.02)
                logging.info(f"Balance after home lose bet: {balance} for {contracts} contracts at {event_response['markets'][0]['no_ask']}")
                no_contracts += contracts


            logging.info(f"Balance before home bet: {kalshi_home_win} Kalshi home lose: {kalshi_home_lose}")
            logging.info(f"Balance after home bet: {balance}")
            logging.info(f"winPer: {winPer}, leverage: {leverage}, expected_runs: {expected_runs}")
            logging.info(
                f"event response home: yes_bid{event_response['markets'][0]['yes_bid']}, "
                f"no_bid{event_response['markets'][0]['no_bid']}, "
                f"yes_ask{event_response['markets'][0]['yes_ask']}, "
                f"no_ask{event_response['markets'][0]['no_ask']}"
            )
            logging.info(
                f"event response away: yes_bid{event_response['markets'][1]['yes_bid']}, "
                f"no_bid{event_response['markets'][1]['no_bid']}, "
                f"yes_ask{event_response['markets'][1]['yes_ask']}, "
                f"no_ask{event_response['markets'][1]['no_ask']}"
            )
        
        except Exception as e:
            logging.error(f"Error processing game state: {e}")
            return




