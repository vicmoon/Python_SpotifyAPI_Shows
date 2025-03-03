import requests
from flask import Flask, render_template, request
# import my_creds 
import os

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


# Get a Spotify API token
def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    
    try:
        auth_response = requests.post(auth_url, {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }, timeout=10)  # Add timeout
        
        if auth_response.status_code != 200:
            print(f"Error getting token: {auth_response.status_code}, {auth_response.text}")
            return None
        
        token = auth_response.json()["access_token"]
        return token
    except Exception as e:
        print(f"Exception in get_spotify_token: {str(e)}")
        return None


# Search for podcasts by keyword
def search_podcasts_by_language(query, markets=["US", "IT", "DE", "RO", "RUS"]):
    all_podcasts = []

    for market in markets:
        params = {
            "q": query,
            "type": "show",
            "limit": 100,  # Reducing from 100 to be safer
            "market": market
        }

        headers = {
            "Authorization": f"Bearer {get_spotify_token()}",
            "Content-Type": "application/json"
        }

        response = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            podcasts = [
                {
                    "name": show["name"],
                    "url": show["external_urls"]["spotify"],
                    "market": market,
                    "id": show["id"]

                }
                for show in data["shows"]["items"]
            ]
            all_podcasts.extend(podcasts)
        else:
            print(f"Error fetching podcasts for language {market}: {response.status_code}, {response.text}")

    return all_podcasts



# Function to get episodes for a podcast
def get_podcast_episodes(show_id):
    episodes_url = f"https://api.spotify.com/v1/shows/{show_id}/episodes"

    headers = {
        "Authorization": f"Bearer {get_spotify_token()}",
        "Content-Type": "application/json"
    }

    response = requests.get(episodes_url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching episodes: {response.status_code}, {response.text}")
        return []

    data = response.json()

    # Extract episode details
    episodes = [
        {"name": episode["name"], "url": episode["external_urls"]["spotify"]}
        for episode in data["items"]
    ]

    return episodes


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/podcasts", methods=["GET"])
def get_podcasts():
    query = request.args.get("query")
    token = get_spotify_token()
    
    if not token:
        # Log token failure
        print("Failed to get Spotify token")
        return render_template("podcasts.html", podcasts=[], error="Authentication failed")
    
    print(f"Searching for: {query} with token: {token[:5]}...")  # Print just first few chars of token
    podcasts = search_podcasts_by_language(query) if query else []
    print(f"Found {len(podcasts)} podcasts")
    
    return render_template("podcasts.html", podcasts=podcasts)




@app.route("/episodes/<show_id>")
def get_episodes(show_id):
    episodes = get_podcast_episodes(show_id)
    return render_template("episodes.html", episodes=episodes)


if __name__ == "__main__":
    app.run(debug=True)
