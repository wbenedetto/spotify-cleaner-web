from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from spotipy import Spotify
import spotipy
from .cleaner.cleaner import runCleaner, getPlaylistLength, getPlaylistSongs
from .cleaner.spotify_auth import get_spotify_oauth
from spotipy.exceptions import SpotifyException

def playlist_info(request):
    uri = request.GET.get('uri')
    
    data = {
        'name': 'Sample Playlist',
        'tracks': 0,
        'image_url': '',
        'owner': 'user'
    }

    return JsonResponse(data)


def login(request):
    request.session.flush()
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


def callback(request):
    code = request.GET.get('code')
    oauth = get_spotify_oauth()
    token_info = oauth.get_access_token(code, as_dict=True)

    request.session['token_info'] = token_info

    return redirect('home')


def get_spotify_client(access_token):
    return spotipy.Spotify(auth=access_token)


def get_valid_token(request):
    token_info = request.session.get("token_info")

    if not token_info:
        return None

    sp_oauth = get_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        request.session['token_info'] = token_info

    return token_info


def logout_view(request):
    request.session.flush()
    return redirect('login')


@csrf_exempt
def home(request):
    token_info = request.session.get('token_info')

    if not token_info:
        return redirect("login")

    try:
        sp = Spotify(auth=token_info["access_token"])
        playlists_raw = sp.current_user_playlists(limit=50)['items']
        playlists = []

        for p in playlists_raw:
            songs = getPlaylistSongs(sp, p['id'])

            playlists.append({
                'name': p['name'],
                'uri': p['uri'],
                'tracks': getPlaylistLength(sp, p['uri']),
                'image_url': p['images'][0]['url'] if p['images'] else None,
                'songs': songs
            })

        return render(request, "home.html", {"playlists": playlists})

    except SpotifyException:
        request.session.flush()
        return redirect("login")


@csrf_exempt
def organize(request):
    if request.method == "POST":
        token_info = request.session.get("token_info")
        if not token_info:
            return redirect("login")
        
        sp = get_spotify_client(token_info["access_token"])
        playlist_uri = request.POST.get("playlist_uri")
        print(f"Organizing: {playlist_uri}")
        message = runCleaner(sp, playlist_uri)
        print(message)
        return redirect("home")