import sys
from PyQt5 import QtWidgets

import deezerDesign
import deezer_api


class DeezerApp(QtWidgets.QMainWindow, deezerDesign.Ui_DeezerWindow):
    def __init__(self, preloaded_playlists):
        super().__init__()
        self.setupUi(self)
        self.preloaded_playlists = preloaded_playlists

        self.deezerHandler = deezer_api.DeezerHandler('DeezerHandlerSettings.ini')
        self.loginAccessToken = ''

        self.loginButton.clicked.connect(self.login)
        self.downloadSingleButton.clicked.connect(self.download_single_playlist)
        self.downloadAllButton.clicked.connect(self.download_all_playlists)
        self.synchronizeButton.clicked.connect(self.synchronize_playlists)
        self.writeLogButton.clicked.connect(self.write_log)

    def login(self):
        self.logWidget.clear()
        self.logWidget.addItem('INFO:\t Authorization process in progress...')
        self.deezerHandler.logging('INFO:\t Authorization process in progress...')
        self.loginAccessToken = self.deezerHandler.get_user_access_token()
        if self.loginAccessToken is not '':
            self.loginLabel.setEnabled(False)
            self.loginButton.setEnabled(False)
            self.downloadSingleLabel.setEnabled(True)
            self.downloadSingleTextEdit.setEnabled(True)
            self.downloadSingleButton.setEnabled(True)
            self.downloadAllLabel.setEnabled(True)
            self.downloadAllButton.setEnabled(True)
            self.synchronizeLabel.setEnabled(True)
            self.synchronizeCheckBox.setEnabled(True)
            self.synchronizeButton.setEnabled(True)
        self.show_log()

    def download_single_playlist(self):
        self.logWidget.clear()
        self.logWidget.addItem('INFO:\t Download single playlist process in progress...')
        self.deezerHandler.logging('INFO:\t Download single playlist process in progress...')
        playlist_name = self.downloadSingleTextEdit.toPlainText()
        user_playlists = self.deezerHandler.get_playlists(self.loginAccessToken)
        check = False
        self.deezerHandler.logging(f'INFO:\t Searching playlist - \"{playlist_name}\"')
        for playlist in user_playlists:
            if playlist_name == playlist.title:
                self.deezerHandler.logging(f'INFO:\t Download playlist - \"{playlist_name}\"')
                self.preloaded_playlists.append(playlist)
                check = True
                break
        if not check:
            self.deezerHandler.logging(f'WARN:\t This playlist name - \"{playlist_name}\" does not exist')
        self.show_log()

    def download_all_playlists(self):
        self.logWidget.clear()
        self.logWidget.addItem('INFO:\t Download all playlists process in progress...')
        self.deezerHandler.logging('INFO:\t Download all playlists process in progress...')
        user_playlists = self.deezerHandler.get_playlists(self.loginAccessToken)
        for playlist in user_playlists:
            self.deezerHandler.logging(f'INFO:\t Download playlist - \"{playlist.title}\"')
            self.preloaded_playlists.append(playlist)
        self.show_log()

    def synchronize_playlists(self):
        self.logWidget.clear()
        self.logWidget.addItem('INFO:\t Synchronize playlists process in progress...')
        self.deezerHandler.logging('INFO:\t Synchronize playlists process in progress...')
        if not self.synchronizeCheckBox.isChecked():
            for playlist in self.preloaded_playlists:
                self.deezerHandler.logging(f'INFO:\t Synchronize playlist - \"{playlist.title}\"')
                self.deezerHandler.add_playlist(playlist, self.loginAccessToken)
        self.show_log()

    def show_log(self):
        self.logWidget.clear()
        for line in self.deezerHandler.log.splitlines():
            self.logWidget.addItem(line)

    def write_log(self):
        self.logWidget.clear()
        self.logWidget.addItem('INFO:\t Write log file process in progress...')
        self.deezerHandler.logging('INFO:\t Write log file process in progress...')
        self.show_log()
        self.deezerHandler.write_log()


def start():
    app = QtWidgets.QApplication(sys.argv)
    window = DeezerApp([])
    window.show()
    app.exec_()


if __name__ == '__main__':
    start()
