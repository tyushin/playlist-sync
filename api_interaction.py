from flask import Flask, request, redirect, url_for
import requests

app = Flask(__name__)


DEEZER_APP_ID = "439942"
DEEZER_APP_SECRET = "20aa27ced2d98642cb2a0007da7daf99"
DEEZER_REDIRECT_URI = "http://127.0.0.1:5000/deezer/login"


class IntermediatePlaylist:
    def __init__(self, playlist_id, title, tracks):
        self.playlist_id = playlist_id
        self.title = title
        self.tracks = tracks


class IntermediateTrack:
    def __init__(self, track_id, title, album_title, artist_name):
        self.track_id = track_id
        self.title = title
        self.album_title = album_title
        self.artist_name = artist_name


@app.route('/', methods=['GET'])
def default():
    url = (f'https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_APP_ID}'
           f'&redirect_uri={DEEZER_REDIRECT_URI}&perms=basic_access,email')
    return redirect(url)


# This path should be your redirect url
@app.route('/deezer/login', methods=['GET'])
def deezer_login():
    global my_access_token
    # retrieve the authorization code given in the url
    code = request.args.get('code')

    # request the access token
    url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={DEEZER_APP_ID}'
           f'&secret={DEEZER_APP_SECRET}&code={code}&output=json')
    response = requests.get(url)

    # If it's not a good code we will get this error
    if response.text == 'wrong code':
        return 'wrong code'

    # We have our access token
    response = response.json()
    global login_access_token
    login_access_token = response['access_token']
    return redirect(url_for('get_playlists'))


@app.route('/playlists', methods=['GET'])
def get_playlists():

    response = requests.get(f'https://api.deezer.com/user/me/playlists', {'access_token': login_access_token})
    response = response.json()

    playlists = []
    for element in response['data']:
        playlist = IntermediatePlaylist(element['id'], element['title'], [])
        playlists.append(playlist)

    for playlist in playlists:
        response = requests.get(f'https://api.deezer.com/playlist/{playlist.playlist_id}/tracks',
                                {'access_token': login_access_token})
        response = response.json()
        tracklist = []
        for element in response['data']:
            track = IntermediateTrack(element['id'], element['title'], element['album']['title'], element['artist']['name'])
            tracklist.append(track)
        playlist.tracks = tracklist

    result = 'Playlists:\n'
    for playlist in playlists:
        result += f'Playlist title: {playlist.title}:\n'
        for track in playlist.tracks:
            result += f'\tTitle: {track.title};\n'
            result += f'\tAlbum title: {track.album_title};\n'
            result += f'\tArtist name: {track.artist_name};\n'

    return result


if __name__ == '__main__':
    app.run()
