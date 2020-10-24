from flask import Flask, request, redirect, url_for
import requests

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
    return redirect(url_for('get_playlists'))


@app.route('/playlists', methods=['GET'])
def get_playlists():
    # Get JSON object (dictionary) for list of user playlists
    response = requests.get(f'https://api.deezer.com/user/me/playlists', {'access_token': login_access_token})
    response = response.json()

    playlists = []
    # Create IntermediatePlaylist model for each playlist in dictionary
    for element in response['data']:
        playlist = IntermediatePlaylist(element['id'], element['title'], [])
        playlists.append(playlist)

    # For each playlist get JSON object (dictionary) for list of playlist tracks
    for playlist in playlists:
        response = requests.get(f'https://api.deezer.com/playlist/{playlist.playlist_id}/tracks',
                                {'access_token': login_access_token})
        response = response.json()

        tracklist = []
        # Create IntermediateTrack model for each track in dictionary
        for element in response['data']:
            track = IntermediateTrack(element['id'], element['title'], element['album']['title'], element['artist']['name'])
            tracklist.append(track)
        # Add list of tracks into IntermediatePlaylist model
        playlist.tracks = tracklist

    # Create string to view result elements
    result = 'Playlists:\n'
    for playlist in playlists:
        result += f'Playlist title: {playlist.title}:\n'
        for track in playlist.tracks:
            result += f'\tTitle: {track.title};\n'
            result += f'\tAlbum title: {track.album_title};\n'
            result += f'\tArtist name: {track.artist_name};\n'

    return result


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

# Add: search tracks, create playlist, add tracks into playlist, exception handler (if cannot do something).

if __name__ == '__main__':
    app.run()
