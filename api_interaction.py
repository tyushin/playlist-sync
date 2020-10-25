from flask import Flask, request, redirect, url_for
import requests
import webbrowser

app = Flask(__name__)


# Settings variables for my application (Setup on official Deezer site)
DEEZER_APP_ID = "439942"
DEEZER_APP_SECRET = "20aa27ced2d98642cb2a0007da7daf99"
DEEZER_REDIRECT_URI = "http://127.0.0.1:5000/deezer/login"


# Class for intermediate playlist model
class IntermediatePlaylist:
    def __init__(self, playlist_id, title, tracks):
        self.playlist_id = playlist_id
        self.title = title
        self.tracks = tracks


# Class for intermediate track model
class IntermediateTrack:
    def __init__(self, track_id, title, album_title, artist_name):
        self.track_id = track_id
        self.title = title
        self.album_title = album_title
        self.artist_name = artist_name


# Default path. Redirect user to authentication service.
@app.route('/', methods=['GET'])
def default():
    url = (f'https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_APP_ID}'
           f'&redirect_uri={DEEZER_REDIRECT_URI}&perms=basic_access,email')
    return redirect(url)


# This path should be your redirect url.
@app.route('/deezer/login', methods=['GET'])
def deezer_login():
    # Retrieve the authorization code given in the url
    code = request.args.get('code')

    # Request the access token
    url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={DEEZER_APP_ID}'
           f'&secret={DEEZER_APP_SECRET}&code={code}&output=json')
    response = requests.get(url)

    # If it's not a good code we will get this error
    if response.text == 'wrong code':
        return 'wrong code'

    # We have our access token
    response = response.json()
    # Global variable for user access token
    global login_access_token
    login_access_token = response['access_token']
    # Redirect user to playlists URL
    return redirect(url_for('get_info'))


# Get all tracks from playlist
def get_tracklist(playlist_id):
    # Get JSON object (dictionary) for list of playlist tracks
    response = requests.get(f'https://api.deezer.com/playlist/{playlist_id}/tracks',
                            {'access_token': login_access_token})
    response = response.json()

    tracklist = []
    # Create IntermediateTrack model for each track in dictionary
    for element in response['data']:
        track = IntermediateTrack(element['id'], element['title'], element['album']['title'], element['artist']['name'])
        tracklist.append(track)
    return tracklist


# Get user playlists
def get_playlists():
    # Get JSON object (dictionary) for list of user playlists
    response = requests.get(f'https://api.deezer.com/user/me/playlists', {'access_token': login_access_token})
    response = response.json()

    playlists = []
    # Create IntermediatePlaylist model for each playlist in dictionary
    for element in response['data']:
        playlist = IntermediatePlaylist(element['id'], element['title'], [])
        playlists.append(playlist)

    # Fill each playlist with tracks
    for playlist in playlists:
        # Add list of tracks into IntermediatePlaylist model
        playlist.tracks = get_tracklist(playlist.playlist_id)

    return playlists


# Search track
def search_track(track_info):
    search_info = ''
    for key, value in track_info.items():
        search_info += f'{key}:\"{value}\" '

    # Get JSON object (dictionary) for searching track
    response = requests.get(f'https://api.deezer.com/search/?q={search_info}', {'access_token': login_access_token})
    response = response.json()

    return response


@app.route('/info', methods=['GET'])
def get_info():
    playlists = get_playlists()

    # Create string to view result elements
    result = 'Playlists:\n'
    for playlist in playlists:
        result += f'Playlist title: {playlist.title}:\n'
        for track in playlist.tracks:
            result += '\t Track:\n'
            result += f'\t\tTitle: {track.title};\n'
            result += f'\t\tAlbum title: {track.album_title};\n'
            result += f'\t\tArtist name: {track.artist_name};\n'
    # TEST
    print(result)

    # TEST for searching tracks
    track_info = {'track': 'Our Story', 'artist': 'Mako'}
    return search_track(track_info)


# Add: search tracks, create playlist, add tracks into playlist, exception handler (if cannot do something).


if __name__ == '__main__':
    # Auto open web page
    webbrowser.open_new_tab("http://127.0.0.1:5000/")
    app.run()
