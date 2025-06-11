import scipy.stats as stats
import time
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

# Example usage:
combined = build_combined_dict()
print(combined[9][0][0][(0,0,0)][-5][(0,0)]) 