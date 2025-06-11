import requests
from bs4 import BeautifulSoup

def fetch_draftkings_mlb_html_data(hT, aT):
    mlb_teams = {
        "ARI": "ARI Diamondbacks",
        "ATL": "ATL Braves",
        "BAL": "BAL Orioles",
        "BOS": "BOS Red",
        "CHC": "CHI Cubs",
        "CWS": "CHI White",
        "CIN": "CIN Reds",
        "CLE": "CLE Guardians",
        "COL": "COL Rockies",
        "DET": "DET Tigers",
        "HOU": "HOU Astros",
        "KC": "KC Royals",
        "LAA": "LA Angels",
        "LAD": "LA Dodgers",
        "MIA": "MIA Marlins",
        "MIL": "MIL Brewers",
        "MIN": "MIN Twins",
        "NYM": "NY Mets",
        "NYY": "NY Yankees",
        "OAK": "OAK Athletics",
        "PHI": "PHI Phillies",
        "PIT": "PIT Pirates",
        "SD": "SD Padres",
        "SEA": "SEA Mariners",
        "SF": "SF Giants",
        "STL": "STL Cardinals",
        "TB": "TB Rays",
        "TEX": "TEX Rangers",
        "TOR": "TOR Blue",
        "WSH": "WAS Nationals"
    }

    home_team = mlb_teams[hT]
    away_team = mlb_teams[aT]
    url = "https://sportsbook.draftkings.com/leagues/baseball/mlb"
    home_team_found = False
    away_team_found = False
    odds = {"home_team": {"line": None, "odds": None}, "away_team": {"line": None, "odds": None}}
    
    # Send a GET request to the website
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all <td> elements with the class 'sportsbook-table__column-row'
        td_elements = soup.find_all('td', class_='sportsbook-table__column-row')
        
        # print(f"Extracted data for teams: {home_team} and {away_team}")
        for td in td_elements:
            # Extract the team name (e.g., "ATL Braves")
            try:
                aria_label = td.find('div', class_='sportsbook-outcome-cell__body').get('aria-label', '')
            except:
                continue
            team_name = ' '.join(aria_label.split(' ')[:2])  # Extract the first two words (e.g., "ATL Braves")
            
            # Check if the team matches the home or away team
            if home_team in team_name and not home_team_found:
                # Extract the spread (e.g., "+1.5")
                spread = td.find('span', class_='sportsbook-outcome-cell__line')
                spread = spread.text.strip() if spread else "N/A"
                
                # Extract the odds (e.g., "+290")
                odds_value = td.find('span', class_='sportsbook-odds')
                odds_value = odds_value.text.strip() if odds_value else "N/A"
                
                # Print the extracted data
                # print(f"Team: {team_name}, Spread: {spread}, Odds: {odds_value}")
                if spread != "N/A":
                    home_team_found = True
                    if spread.startswith('+'):
                        spread = float(spread[1:])
                        odds["home_team"]["line"] = spread
                    else:
                        spread = float(spread[1:])
                        odds["home_team"]["line"] = spread*-1
                    if odds_value.startswith('+'):
                        odds_value = float(odds_value[1:])
                        odds["home_team"]["odds"] = odds_value
                    else:
                        odds_value = float(odds_value[1:])
                        odds["home_team"]["odds"] = odds_value*-1


            if away_team in team_name and not away_team_found:
                # Extract the spread (e.g., "+1.5")
                spread = td.find('span', class_='sportsbook-outcome-cell__line')
                spread = spread.text.strip() if spread else "N/A"
                
                # Extract the odds (e.g., "+290")
                odds_value = td.find('span', class_='sportsbook-odds')
                odds_value = odds_value.text.strip() if odds_value else "N/A"
                
                # Print the extracted data
                # print(f"Team: {team_name}, Spread: {spread}, Odds: {odds_value}")
                if spread != "N/A":
                    if spread.startswith('+'):
                        spread = float(spread[1:])
                        odds["away_team"]["line"] = spread
                    else:
                        spread = float(spread[1:])
                        odds["away_team"]["line"] = spread*-1
                    if odds_value.startswith('+'):
                        odds_value = float(odds_value[1:])
                        odds["away_team"]["odds"] = odds_value
                    else:
                        odds_value = float(odds_value[1:])
                        odds["away_team"]["odds"] = odds_value*-1
            if home_team_found and away_team_found:
                break
        
        # Save the raw HTML to a file (optional)
        with open('draftkings_mlb_data.html', 'w') as html_file:
            html_file.write(soup.prettify())
        
        # print("\nHTML data successfully fetched and saved to draftkings_mlb_data.html")
    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
    return odds

if __name__ == "__main__":
    fetch_draftkings_mlb_html_data("BOS", "LAA")
    