import sys
import os
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

import requests
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.db_config import DATABASE_URL
from src.db.models.team import Team
from src.db.models.player import Player
    
def fetch_fpl_data():
    """Fetch data from FPL API"""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    return response.json()

def get_position_from_element_type(element_type):
    """Convert FPL element type to position"""
    positions = {
        1: 'Goalkeeper',
        2: 'Defender',
        3: 'Midfielder',
        4: 'Forward'
    }
    return positions.get(element_type, 'Unknown')

def preview_data(teams_data, players_data):
    """Preview the data that will be inserted"""
    print("\n=== Teams to be added ===")
    for team in teams_data:
        print(f"- {team['name']} ({team['league']}, {team['country']})")
    
    print("\n=== Players to be added ===")
    for player in players_data:
        print(f"- {player['name']} ({player['position']}) - Team ID: {player['team_id']}")
    
    print(f"\nTotal teams to add: {len(teams_data)}")
    print(f"Total players to add: {len(players_data)}")

def main():
    # Create database engine and session
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Fetch FPL data
        print("Fetching FPL data...")
        fpl_data = fetch_fpl_data()
        
        # Create a mapping of FPL team IDs to our team IDs
        team_id_mapping = {}
        teams_data = []
        players_data = []
        
        # Process teams data
        print("Processing teams data...")
        for team in fpl_data['teams']:
            team_data = {
                'name': team['name'],
                'league': 'Premier League',
                'country': 'England',
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            teams_data.append(team_data)
            new_team = Team(**team_data)
            session.add(new_team)
            session.flush()  # Flush to get the generated ID
            team_id_mapping[team['id']] = new_team.id
        
        # Process players data
        print("Processing players data...")
        for player in fpl_data['elements']:
            player_data = {
                'name': f"{player['first_name']} {player['second_name']}",
                'position': get_position_from_element_type(player['element_type']),
                'team_id': team_id_mapping.get(player['team']),  # Use our team ID
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            players_data.append(player_data)
            new_player = Player(**player_data)
            session.add(new_player)
        
        # Preview the data
        preview_data(teams_data, players_data)
        
        # Ask for confirmation
        while True:
            response = input("\nDo you want to commit these changes? (yes/no): ").lower()
            if response in ['yes', 'y']:
                session.commit()
                print("Changes committed successfully!")
                break
            elif response in ['no', 'n']:
                session.rollback()
                print("Changes rolled back.")
                break
            else:
                print("Please answer 'yes' or 'no'")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main() 