import requests
from flask import Flask, render_template, request
# import my_creds 
import os

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
EPISODES_PER_PAGE = 15

# CLIENT_ID = my_creds.CLIENT_ID
# CLIENT_SECRET = my_creds.CLIENT_SECRET




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
def search_podcasts_by_language(query, markets=["US", "IT", "DE", "RO"]):
    all_podcasts = []

    for market in markets:
        params = {
            "q": query,
            "type": "show",
            "limit": 50,  # Reducing from 100 to be safer
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

    return all_podcasts, markets



# Function to get episodes for a podcast
def get_podcast_episodes(show_id):
    page = request.args.get("page", 1, type=int)  # Get page number
    limit = 10  # Number of episodes per page
    offset = (page - 1) * limit  # Calculate offset

    episodes_url = f"https://api.spotify.com/v1/shows/{show_id}/episodes?limit={limit}&offset={offset}"

    headers = {
        "Authorization": f"Bearer {get_spotify_token()}",
        "Content-Type": "application/json"
    }

    response = requests.get(episodes_url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching episodes: {response.status_code}, {response.text}")
        return [], False  # Return empty list and no pagination

    data = response.json()

    episodes = [
        {"name": episode["name"], "url": episode["external_urls"]["spotify"]}
        for episode in data.get("items", [])
    ]

    has_next_page = data.get("next") is not None  # Check if more episodes exist

    return episodes, has_next_page  # Return both episodes and pagination flag


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

    markets = ["US", "IT", "DE", "RO"]
    
    if query:
        result = search_podcasts_by_language(query, markets)
        if isinstance(result, tuple) and len(result) == 2:
            podcasts, _ = result
        else:
                # If function doesn't return markets as expected
            podcasts = result
    else:
        podcasts = []

    print(f"Found {len(podcasts)} podcasts")
    
    return render_template("podcasts.html", podcasts=podcasts, markets=markets)




@app.route("/episodes/<show_id>")
def get_episodes(show_id):
    page = request.args.get("page", 1, type=int)
    query = request.args.get("query")

    if not query:
        # Redirect back to podcasts page if query is missing
        return redirect(url_for("get_podcasts"))
    
    episodes, has_next_page = get_podcast_episodes(show_id)

    return render_template(
        "episodes.html",
        episodes=episodes,
        show_id=show_id,
        page=page,
        has_next_page=has_next_page,
        query=query
    )


if __name__ == "__main__":
    app.run(debug=True)
