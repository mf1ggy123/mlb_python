import scipy.stats as stats
import ast


def set_nested_dict(d, keys, value):
    # print(f"Setting nested dict with keys: {keys} and value: {value}")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value
    # print(f"Nested dict set: {d}")
    # time.sleep(1)

def read_stats_with_balls_strikes(file_path):
    """
    Reads the file statswithballsstrikes and saves the data in a nested dictionary.
    If any inning is greater than 10, it is set to 10.
    """
    data_dict = {}

    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    key_str, value = line.split(':', 1)
                    key_tuple = parse_key(key_str.strip())
                    # Unpack the tuple into the nested structure
                    inning, home_away, outs, base_positions, score_diff, balls_strikes = key_tuple
                    # Set inning to 10 if greater than 10
                    if inning > 10:
                        inning = 10
                    keys = [inning, home_away, outs, base_positions, score_diff, balls_strikes]
                    won_games, total_games = ast.literal_eval(value.strip())
                    percentage = won_games / total_games if total_games != 0 else 0.0
                    if home_away == 0:
                        percentage = 1 - percentage
                        score_diff = -score_diff
                    set_nested_dict(data_dict, keys, percentage)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return data_dict

def read_leverage_index(file_path):
    """
    Reads the file leverageindex and saves the data in a nested dictionary.
    The key is a tuple: (inning, home_away, outs, bases_tuple, score_diff, balls_strikes_tuple)
    The value is the leverage index.
    """
    data_dict = {}

    bases_dict={
        '1': (0, 0, 0),
        '2': (1, 0, 0),
        '3': (0, 1, 0),
        '4': (1, 1, 0),
        '5': (0, 0, 1),
        '6': (1, 0, 1),
        '7': (0, 1, 1),
        '8': (1, 1, 1),
    }

    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    # Split by comma and parse values
                    parts = line.split(',')
                    if len(parts) == 6:
                        inning = int(parts[1])
                        if parts[0] == '"H"':
                            home_away = 1
                        else:
                            home_away =  0  # Assuming 'H' for home and 'A' for away
                        outs = int(parts[2])
                        bases = bases_dict[parts[3]]
                        if home_away == 0:
                            score_diff = -int(parts[4])
                        else:
                            score_diff = int(parts[4])
                        leverage = float(parts[5])
                        # You may want to convert inning and bases to appropriate types/tuples
                        keys = [inning, home_away, outs,  bases, score_diff]
                        set_nested_dict(data_dict, keys, leverage)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return data_dict


def read_runs_per_inning_balls_strikes_stats(file_path):
    """
    Reads the file runsperinningballsstrikesstats and saves the data in a nested dictionary.
    The key is a tuple: (outs, bases_tuple, balls_strikes_tuple)
    The value is a list of run counts.
    """
    data_dict = {}

    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    
                    key_str, value_str = line.split(':', 1)
                    key = ast.literal_eval(key_str.strip())
                    outs = int(key[0])
                    bases = key[1]
                    balls_strikes = key[2]
                    value = ast.literal_eval(value_str.strip())
                    total = 0
                    for i in range(len(value)):
                        total += value[i]*i
                    keys = [outs,  bases, balls_strikes]
                    set_nested_dict(data_dict, keys, total/sum(value))
                    
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return data_dict


def parse_key(key_str):
    # Example key_str: "(14, 1, 2, (1, 0, 1), -3, (2, 2))"
    return ast.literal_eval(key_str)

def build_combined_dict():
    stats_dict = read_stats_with_balls_strikes('./statswithballsstrikes')
    leverage_dict = read_leverage_index('./leverage')
    runs_dict = read_runs_per_inning_balls_strikes_stats('./runsperinningballsstrikesstats')

    combined_dict = {}

    for inning in stats_dict:
        for home_away in stats_dict[inning]:
            for outs in stats_dict[inning][home_away]:
                for base_positions in stats_dict[inning][home_away][outs]:
                    for score_diff in stats_dict[inning][home_away][outs][base_positions]:
                        for balls_strikes in stats_dict[inning][home_away][outs][base_positions][score_diff]:
                            stats_val = stats_dict[inning][home_away][outs][base_positions][score_diff][balls_strikes]
                            # Try to get leverage_val and runs_val, use None if not found
                            try:
                                leverage_val = leverage_dict[inning][home_away][outs][base_positions][score_diff]
                            except Exception:
                                leverage_val = None
                            try:
                                runs_val = runs_dict[outs][base_positions][balls_strikes]
                            except Exception:
                                runs_val = None
                            # Build the nested structure
                            combined_dict \
                                .setdefault(inning, {}) \
                                .setdefault(home_away, {}) \
                                .setdefault(outs, {}) \
                                .setdefault(base_positions, {}) \
                                .setdefault(score_diff, {})[balls_strikes] = (stats_val, leverage_val, runs_val)
    return combined_dict

# runs_per_inning_stats = read_runs_per_inning_balls_strikes_stats('runsperinningballsstrikesstats')
# print(runs_per_inning_stats)  # Example usage
def calculate_expected_margin(home_spread, away_spread, home_odds, away_odds, std_dev=3):
    """
    Calculate expected run margin that the away team wins by given spreads and odds.

    Parameters:
    - home_spread (float): Spread for home team (e.g. +2.5)
    - away_spread (float): Spread for away team (e.g. -2.5)
    - home_odds (int): American odds for home spread (e.g. -188)
    - away_odds (int): American odds for away spread (e.g. +145)
    - std_dev (float): Standard deviation of margin of victory (default 3)

    Returns:
    - float: Expected margin of victory for away team
    """
    def american_to_prob(odds):
        if odds < 0:
            return -odds / (-odds + 100)
        else:
            return 100 / (odds + 100)

    def normalize_probs(prob_home, prob_away):
        total = prob_home + prob_away
        return prob_home / total, prob_away / total

    # Convert odds to implied probabilities
    prob_home = american_to_prob(home_odds)
    prob_away = american_to_prob(away_odds)

    # Normalize probabilities to remove vig
    prob_home_norm, prob_away_norm = normalize_probs(prob_home, prob_away)

    # We use the away spread and probability away covers to calculate expected margin
    # Probability margin <= away_spread = 1 - P(away covers)
    prob_less_equal = 1 - prob_away_norm

    # Find z-score corresponding to that cumulative probability
    z = stats.norm.ppf(prob_less_equal)

    # Calculate expected mean margin (away team)
    if away_odds < home_odds:
        mu = away_spread - z * std_dev
    else:
        mu = away_spread + z * std_dev

    return mu


# # Example usage:
# home_spread = +2.5
# away_spread = -2.5
# home_odds = +145
# away_odds = -188

# expected_margin = calculate_expected_margin(home_spread, away_spread, home_odds, away_odds)
# print(f"Expected run margin (away team wins by):", expected_margin, "runs")

def kelly_criterion(p, price, bankroll, fraction=1.0):
    """
    Calculates the optimal bet size using the Kelly Criterion.

    Parameters:
    - p (float): Your estimated probability of winning (e.g. 0.78).
    - price (float): Price to buy the contract (e.g. 0.65 for Kalshi YES).
    - bankroll (float): Total bankroll available (e.g. 100).
    - fraction (float): Fraction of Kelly to use (e.g. 0.5 for half-Kelly).

    Returns:
    - optimal_bet (float): Dollar amount to bet.
    - num_contracts (int): How many contracts to buy.
    - expected_value (float): Expected value per contract.
    """
    b = (1 - price) / price  # net odds
    q = 1 - p
    kelly_fraction = (b * p - q) / b

    # Ensure it's non-negative (no bet if negative edge)
    if kelly_fraction <= 0:
        return 0.0, 0, (p * 1.0 + q * -price)

    # Apply fractional Kelly if desired
    kelly_fraction *= fraction
    optimal_bet = bankroll * kelly_fraction
    expected_value = (p * 1.0) + (q * -price)

    return round(optimal_bet, 2), round(expected_value, 3)

def dynamic_kelly_fraction(
    win_prob: float,
    inning: int,
    leverage_index: float,
    model_confidence: float
) -> float:
    """
    Determines an appropriate Kelly fraction based on game state.

    Parameters:
    - win_prob (float): Your estimated probability (0–1)
    - inning (int): Current inning (1–9+)
    - leverage_index (float): LI for current moment (avg ~1.0)
    - model_confidence (float): Your confidence in the model (0–1)

    Returns:
    - fraction (float): Adjusted Kelly fraction (0–1)
    """
    # Start with full Kelly
    base_fraction = 1.0

    # Discount early game: more uncertainty
    if inning <= 3:
        base_fraction *= 0.5
    elif inning <= 6:
        base_fraction *= 0.75

    # Discount high-leverage moments to reduce variance
    if leverage_index >= 2:
        base_fraction *= 0.5
    elif leverage_index >= 1.5:
        base_fraction *= 0.75

    # Discount based on confidence
    base_fraction *= model_confidence

    # Cap at 1.0 and minimum of 0
    return max(0.0, min(base_fraction, 1.0))

