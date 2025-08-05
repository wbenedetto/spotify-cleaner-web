from .GPT_client import client
#from .spotify_auth import sp
import random


def fetchPlaylists(sp):
    userPlaylists = {}
    playlists = sp.current_user_playlists(limit=50, offset=0)
    for playlist in playlists['items']:
        userPlaylists.setdefault(playlist['name'], playlist['uri'])
    return userPlaylists

def findURI(sp, title, artist=None,):
    if artist:
        songSearch = sp.search(q=f'track:{title} artist:{artist}', type='track', limit=1)
    else:
        songSearch = sp.search(q=f'artist:{title}', type='track', limit=1)
    URI = songSearch['tracks']['items'][0]['uri']
    return URI

def addSong(sp, playlistURI, name, artist=None):
    sp.playlist_add_items(playlistURI, [findURI(name, artist)], position=None)

def removeSong(sp, playlistURI, name, artist=None):
    sp.playlist_remove_all_occurrences_of_items(playlistURI, [findURI(name, artist)], snapshot_id=None)

def getPlaylistSongs(sp, playlistURI):
    playlistSongs = []
    offset = 0
    limit = 100

    while True:
        results = sp.playlist_tracks(playlistURI, limit=limit, offset=offset)
        items = results.get('items', [])
        if not items:
            break

        for item in items:
            track = item.get("track")
            if track:
                playlistSongs.append({
                    'name': track.get("name", "Unknown Title"),
                    'artist': track['artists'][0]['name'] if track.get('artists') else 'Unknown Artist',
                    'album': track['album']['name'] if track.get('album') else 'Unknown Album'
                })

        offset += limit

    return playlistSongs

def getPlaylistLength(sp, playlistURI):
    data = sp.playlist(playlistURI, fields='tracks.total')
    return data['tracks']['total']



def getPlaylistArtists(sp, playlistURI):
    playlistArtists = []
    artists = sp.playlist_tracks(playlistURI, fields='items.track.artists.name', limit=None, offset=0)
    for item in artists['items']:
        playlistArtists.append(item['track']['artists'][0]['name'])
    return playlistArtists

def uploadGPT(uriList, prompt):
    formatted = '\n'.join(uriList)
    response = client.responses.create(
        model="gpt-4.1",
        input=f"Here is a list of my playlist songs (URIs):\n\n{formatted}\n\n{prompt}. Return only a reordered list of URIs, nothing else."
    )
    return response.output_text

def randomizePlaylist(sp, playlistURI):
    songs = getPlaylistSongs(playlistURI)
    indexList = list(range(len(songs)))
    random.shuffle(indexList)
    for i in range(len(songs)):
        sp.playlist_reorder_items(playlistURI, range_start=i, insert_before=indexList[i], range_length=1)

def createOrderKey(songs):
    removedLines = songs.split('\n')
    orderList = []
    for i in range(1, len(removedLines)):
        item = removedLines[i]
        removedCommas = item.split(',')
        artist = removedCommas[0].strip()
        title = ','.join(removedCommas[1:]).strip()
        orderList.append((title, artist))
    orderListDict = dict(orderList)
    return orderListDict

def reorderPlaylist(sp, playlistURI, uriList):
    for uri in uriList:
        print(f"Re-adding: {uri}")
        sp.playlist_remove_all_occurrences_of_items(playlistURI, [uri])
        sp.playlist_add_items(playlistURI, [uri])

def createURIList(sp, playlistURI):
    data = sp.playlist_items(playlistURI)
    if not data or 'items' not in data:
        print("Error: Could not fetch playlist items.")
        return []
    
    uris = []
    for item in data['items']:
        track = item.get('track')
        if track and track.get('uri'):
            uris.append(track['uri'])
        else:
            print("Skipped item with missing track:", item)
    
    return uris

prompts = [
    'Can you sort these by release date?',
    'Can you make some song recommendations based on my playlist. Return song names and artists as pairs.',
    'Can you place these in an order that makes sense to listen to them in as if they were all in the same album?'
]

def runCleaner(sp, playlistURI):
    try:
        print("Getting original playlist URIs...")
        originalURIs = createURIList(sp, playlistURI)

        print("Sending URIs to GPT for reordering...")
        newOrderText = uploadGPT(originalURIs, prompts[2])
        newOrderURIs = [line.strip() for line in newOrderText.split('\n') if line.strip().startswith("spotify:track:")]

        print("Reordered URIs:")
        print(newOrderURIs)

        print("Applying new order...")
        reorderPlaylist(sp, playlistURI, newOrderURIs)

        return "Playlist reordered successfully."

    except Exception as e:
        return f"Error during cleaner run: {e}"

#git test