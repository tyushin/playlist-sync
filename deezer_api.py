import socket
import requests
import webbrowser
import configparser
import datetime


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


class DeezerHandler:
    def __init__(self, settings_path):
        """
        Class constructor

        :param settings_path: Path to file with settings
        """
        settings = configparser.ConfigParser()
        settings.read(settings_path)

        # Settings variables for logger
        self.log_path = settings.get('path', 'log')
        date = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        self.log = f'Create Datetime - \"{date}\"\n'

        # Settings variables for my application (Setup on official Deezer site)
        self.logging(f'INFO:\t Initialized settings variables for deezer application')
        self.deezer_app_id = settings.get('application', 'deezer_app_id')
        self.deezer_app_secret = settings.get('application', 'deezer_app_secret')
        self.deezer_redirect_uri = settings.get('application', 'deezer_redirect_uri')

        # Settings variables for socket listener
        self.logging(f'INFO:\t Initialized settings variables for socket listener')
        self.host = settings.get('socket', 'host')
        self.port = int(settings.get('socket', 'port'))

    def response_handler(self, status_code):
        """
        Handles the response

        :param status_code: Status code of response
        """

        if status_code == 200:
            self.logging(f'INFO:\t Status code: {status_code} - Successful operation')
        elif status_code == 300:
            self.logging(f'ERROR:\t Status code: {status_code} - OAuthException (TOKEN_INVALID)')
        elif status_code == 500:
            self.logging(f'ERROR:\t Status code: {status_code} - ParameterException (PARAMETER)')
        elif status_code == 501:
            self.logging(f'ERROR:\t Status code: {status_code} - MissingParameterException (PARAMETER_MISSING)')
        elif status_code == 600:
            self.logging(f'ERROR:\t Status code: {status_code} - InvalidQueryException (QUERY_INVALID)')
        elif status_code == 700:
            self.logging(f'ERROR:\t Status code: {status_code} - Exception (SERVICE_BUSY)')
        elif status_code == 800:
            self.logging(f'ERROR:\t Status code: {status_code} - DataException (DATA_NOT_FOUND)')
        elif status_code == 901:
            self.logging(f'ERROR:\t Status code: {status_code} - IndividualAccountChangedNotAllowedException '
                         f'(INDIVIDUAL_ACCOUNT_NOT_ALLOWED)')

    def get_user_access_token(self):
        """
        Get user access token

        :return: access_token
        """

        self.logging(f'INFO:\t Getting user access token')
        self.logging(f'INFO:\t Redirecting to registration link')
        url = (f'https://connect.deezer.com/oauth/auth.php?app_id={self.deezer_app_id}'
               f'&redirect_uri={self.deezer_redirect_uri}&perms=manage_library,email')
        webbrowser.open_new_tab(url)
        self.logging(f'INFO:\t Opening a socket to accept a response')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(1)
            conn, addr = s.accept()
            data = conn.recv(64)
        self.logging(f'INFO:\t Getting code of response')
        code = str(data).split(' ')[1].split('=')[1]
        self.logging(f'INFO:\t Trying to get an access token')
        url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={self.deezer_app_id}'
               f'&secret={self.deezer_app_secret}&code={code}&output=json')
        response = requests.get(url)
        self.response_handler(response.status_code)

        if response.text == 'wrong code':
            self.logging(f'ERROR:\t Wrong code of response - \"{code}\"')

        # Get access token
        response = response.json()
        return response['access_token']

    def get_tracklist(self, playlist_id, access_token):
        """
        Get all tracks from playlist

        :param playlist_id:
        :param access_token:
        :return: [IntermediateTrack]
        """

        self.logging(f'INFO:\t Trying to get JSON object (dictionary) with list of tracks for playlist - '
                     f'\"{playlist_id}\"')
        response = requests.get(f'https://api.deezer.com/playlist/{playlist_id}/tracks', {'access_token': access_token})
        self.response_handler(response.status_code)
        response = response.json()

        tracklist = []
        self.logging(f'INFO:\t Creating an IntermediateTrack model for each track in the response dictionary')
        for element in response['data']:
            track = IntermediateTrack(element['id'], element['title'], element['album']['title'],
                                      element['artist']['name'])
            tracklist.append(track)
        return tracklist

    def get_playlists(self, access_token):
        """
        Get user playlists

        :param access_token:
        :return: [IntermediatePlaylist]
        """

        self.logging(f'INFO:\t Trying to get JSON object (dictionary) with list of user playlists')
        response = requests.get(f'https://api.deezer.com/user/me/playlists', {'access_token': access_token})
        self.response_handler(response.status_code)
        response = response.json()

        playlists = []
        self.logging(f'INFO:\t Creating an IntermediatePlaylist model for each playlist in dictionary')
        for element in response['data']:
            playlist = IntermediatePlaylist(element['id'], element['title'], [])
            playlists.append(playlist)

        self.logging(f'INFO:\t Fill each playlist with tracks')
        for playlist in playlists:
            # Add list of tracks into IntermediatePlaylist model
            playlist.tracks = self.get_tracklist(playlist.playlist_id, access_token)

        return playlists

    def playlists_to_string(self, playlists):
        """
        Create string to view list of Playlists

        :param playlists:
        :return: string_playlists
        """

        self.logging(f'INFO:\t Converting list of IntermediatePlaylist model to string')
        string_playlists = 'Playlists:\n'
        for playlist in playlists:
            string_playlists += f'Playlist title: {playlist.title}:\n'
            for track in playlist.tracks:
                string_playlists += '\t Track:\n'
                string_playlists += f'\t\tTitle: {track.title};\n'
                string_playlists += f'\t\tAlbum title: {track.album_title};\n'
                string_playlists += f'\t\tArtist name: {track.artist_name};\n'
        return string_playlists

    def create_playlist(self, playlist_title, access_token):
        """
        Create playlist

        :param playlist_title:
        :param access_token:
        """

        self.logging(f'INFO:\t Trying to get user ID')
        response = requests.get(f'https://api.deezer.com/user/me', {'access_token': access_token})
        self.response_handler(response.status_code)
        response = response.json()
        user_id = response['id']

        self.logging(f'INFO:\t Trying to create playlist with title - \"{playlist_title}\"')
        response = requests.post(fr'https://api.deezer.com/user/{user_id}/playlists',
                                 {'access_token': access_token,
                                  'title': playlist_title,
                                  'request_method': 'POST'})
        self.response_handler(response.status_code)

    def add_track(self, playlist_id, track_id, access_token):
        """
        Add track to playlist

        :param playlist_id:
        :param track_id:
        :param access_token:
        """

        self.logging(f'INFO:\t Post track - \"{track_id}\" into user playlist - \"{playlist_id}\"')
        response = requests.post(fr'https://api.deezer.com/playlist/{playlist_id}/tracks',
                                 {'access_token': access_token,
                                  'songs': track_id,
                                  'request_method': 'POST'})
        self.response_handler(response.status_code)

    def add_playlist(self, playlist, access_token):
        """
        Add playlist

        :param playlist: IntermediatePlaylist
        :param access_token:
        """

        self.logging(f'INFO:\t Trying add playlist - \"{playlist.title}\"')
        self.logging(f'INFO:\t Check for availability this playlist in user library')
        available_playlists = self.get_playlists(access_token)
        exist_title = False
        for element in available_playlists:
            if element.title == playlist.title:
                exist_title = True
                break
        self.logging(f'INFO:\t Playlist availability status - \"{exist_title}\"')
        if not exist_title:
            self.create_playlist(playlist.title, access_token)
            available_playlists = self.get_playlists(access_token)

        self.logging(f'INFO:\t Trying to update the tracks in the playlist')
        for element in available_playlists:
            if element.title == playlist.title:
                for track in playlist.tracks:
                    self.add_track(element.playlist_id, self.search_track(track), access_token)
                break

    def search_track(self, track):
        """
        Search track

        :param track: IntermediateTrack
        :return: track_id
        """

        self.logging(f'INFO:\t Trying to get JSON object (dictionary) with info for searching track - '
                     f'\"{track.title}\"')
        search_info = f'artist:\"{track.artist_name}\" album:\"{track.album_title}\" track:\"{track.title}\"'
        response = requests.get(f'https://api.deezer.com/search/?q={search_info}')
        self.response_handler(response.status_code)
        response = response.json()
        self.logging(f'INFO:\t Trying to choose the required track')
        if response['total'] != 0:
            result_position = 0
            for position, element in enumerate(response['data']):
                if track.title == element['title']:
                    result_position = position
                    break
            self.logging(f'INFO:\t Track was found')
            return response['data'][result_position]['id']
        else:
            self.logging(f'INFO:\t Track with title - \"{track.title}\", artist name - \"{track.artist_name}\",'
                         f' album title - \"{track.album_title}\" was not found')
            return 0

    def logging(self, message):
        """
        Write information to logger

        :param message:
        """

        self.log += f'{message}\n'

    def write_log(self):
        """
        Write logger to file (path set in settings file)
        """

        date = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        log_file_name = f'{self.log_path}_{date}.log'
        self.logging(f'INFO:\t Writing log file to - {log_file_name}.')
        with open(log_file_name, 'w') as file:
            file.write(self.log)


if __name__ == '__main__':
    deezer_handler = DeezerHandler('DeezerHandlerSettings.ini')
    login_access_token = deezer_handler.get_user_access_token()
    test_track_first = IntermediateTrack('', 'Miracle', 'Miracle', 'CHVRCHES')
    test_track_second = IntermediateTrack('', 'Like It Is', 'Like It Is', 'Kygo')
    test_playlist = IntermediatePlaylist('', 'New_Test', [test_track_first, test_track_second])
    user_playlists = deezer_handler.get_playlists(login_access_token)
    print(deezer_handler.playlists_to_string(user_playlists))
    deezer_handler.add_playlist(test_playlist, login_access_token)
    deezer_handler.write_log()
