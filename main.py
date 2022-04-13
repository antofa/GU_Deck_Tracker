# -*- coding: utf8 -*-

###########
# Imports #
###########

from time import sleep
import sys
import webbrowser
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
import getpass
import os
import urllib.request
import re
import subprocess
import json
import pydash as py_
from pprint import pprint

from utils.net import getDeckFromAPI
from utils.player import Player
from utils.globals import GU_DATA, ENCODING, GU_DECKS_PLAYER_PAGE_BASE
from utils.deck import ROW_LENGTH
from version import VERSION as localVersion

#########################
# Global variables      #
#########################

player = None
opponent = None
playerId = None
opponentId = None
gameId = None
firstPlayerId = None
localLowPath = f'{os.getenv("APPDATA")}/../LocalLow/'
guLogPath = './FuelGames/gods/logs/latest/'
netDataSyncFilePath = f'{localLowPath}{guLogPath}/netdatasync_client/netdatasync_client_info.txt'
combatRecorderFilePath = f'{localLowPath}{guLogPath}/Combat_Recorder/Combat_Recorder_info.txt'
assetDownloaderFilePath = f'{localLowPath}{guLogPath}/asset_downloader/asset_downloader_info.txt'
eventSolverFilePath = f'{localLowPath}{guLogPath}/event_solver/event_solver_info.txt'
playerInfoFilePath = f'{localLowPath}{guLogPath}/player/player_info.txt'
# gameNetworkManagerFilePath = f'{localLowPath}{guLogPath}/GameNetworkManager/GameNetworkManager_info.txt'
outputLogSimpleFilePath = f'{localLowPath}{guLogPath}/../../output_log_simple.txt'

#########################
# PyInstaller Functions #
#########################

# Taken from: https://www.titanwolf.org/Network/q/8250536f-04b3-423a-8833-b76bf07cdb89/y
# This is needed to wrap text files into the .exe while still allowing the tracker to be used in .py form
# Input: Relative path to a file that will be wrapped in the .exe file
# Output: Valid path to that file whether or not it's wrapped in the .exe file


def resource_path(rel_path):
    # This is the path added when run in the .exe file
    try:
        base_path = sys._MEIPASS

    # This throws an exception when not in the .exe, so just use the local directory
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, rel_path)

####################
# Config Functions #
####################


# Input: Config file, line of config to update, and the value to update it to.
# Output: Just returns the updatedValue input
# Additional functionality: Updates the config file
def updateConfig(configFile, lineToChange, updatedValue):
    conFile = open(configFile, "r", encoding=ENCODING)
    lines = conFile.readlines()
    conFile.close()

    found = False
    for n in range(len(lines)):
        if (lines[n].split("::==")[0] == lineToChange):
            lines[n] = lineToChange + "::==" + str(updatedValue) + "\n"
            found = True
            break

    # If the value to change doesn't exist, return -1
    if (not found):
        return -1

    conFile = open(configFile, "w", encoding=ENCODING)
    conFile.writelines(lines)
    conFile.close()

    return updatedValue

# config.txt Line Number -> Value:
#   0 -> Text Font (textFont)
#   1 -> Text Size (textSize)
#   2 -> Opacity (opacity)
#   3 -> Log File Path (logFolderPath)
#   4 -> Show Deck Tracker (deckTracker)
# Input: Config file and the line of config to return (see above for correct line)
# Output: The requested value


def getConfigVal(configFile, lineHeader):
    conFile = open(configFile, "r", encoding=ENCODING)
    lines = conFile.readlines()
    conFile.close()

    for line in lines:
        splitLines = line.split("::==")
        if (splitLines[0] == lineHeader):
            return splitLines[1].strip()

    # We didn't find the header
    return -1


#####################
# Tracker Functions #
#####################

# Output: None
# Additional Functionality: Opens the opponent's gudecks page in a new tab of their default browser
def getOpponentWebpage(logFolderPath):
    global opponentId

    if (not opponentId):
        return -1

    webbrowser.open((f'{GU_DECKS_PLAYER_PAGE_BASE}{opponentId}'), new=2, autoraise=True)
    return 1


def getOpponentDeck():
    if (opponent.hasDeckList):
        return

    opponentGod = None

    global outputLogSimpleFilePath
    with open(outputLogSimpleFilePath, "r", encoding=ENCODING) as f:
        file = f.read()
        opponentGod = re.findall("Set God Color: (\w+)", file)[-1].lower()

    print('getOpponentDeck', opponentId, opponentGod)

    (deck, archetype, stats) = getDeckFromAPI(opponentId, opponentGod, useMock=False)
    [god, *cardIds] = deck.split(',')

    return (god, cardIds, archetype, stats)


# Output: A list of tuples representing the player's starting deck
# Error codes: -1 -> No valid file found; -2 -> No deck within file found
def getStartingCardIds():
    global assetDownloaderFilePath

    # Can't find the log file for some reason
    if (not os.path.exists(assetDownloaderFilePath)):
        return -1

    with open(assetDownloaderFilePath, "r", encoding=ENCODING) as assetFile:
        numCardsFound = 0
        artIdList = []

        for line in assetFile:
            if ("LoadOrDownloadAssetBundle: " in line):
                artId = line.split("LoadOrDownloadAssetBundle: ")[1].strip()
                artIdList.append(artId.upper())
                numCardsFound += 1

            # player deck = first 30 cards
            if (numCardsFound == 30):
                break

    cardIds = []

    for artId in artIdList:
        card = py_.find(GU_DATA["records"], lambda x: x["art_id"] == artId)
        cardIds.append(card["id"])

    print('cardIds', cardIds)

    return cardIds


def getDecksStr():
    global playerId, opponentId, player, opponent

    if not playerId or not opponentId:
        return ''

    playerDeckLines = str(player.deck).split('\n')
    opponentDeckLines = str(opponent.deck).split('\n')

    spacer = ' ' * ROW_LENGTH
    rows = []

    for index in range(max([len(playerDeckLines), len(opponentDeckLines)])):
        rows.append(f'{py_.get(playerDeckLines, index, spacer): ^{ROW_LENGTH}}{py_.get(opponentDeckLines, index, spacer): >{ROW_LENGTH}}')

    return "\n".join(rows)


def resetPlayersData():
    print('resetPlayersData')
    global playerId, opponentId, firstPlayerId, player, opponent
    playerId = opponentId = firstPlayerId = player = opponent = None


def setPlayers():
    global playerId, opponentId
    if playerId and opponentId:
        return

    try:
        global outputLogSimpleFilePath
        with open(outputLogSimpleFilePath, "r", encoding=ENCODING) as f:
            file = f.read()
            r = re.search('p:PlayerInfo\(apolloId: (\d+).* o:PlayerInfo\(apolloId: (\d+)', file, re.MULTILINE).groups()

            playerId = int(r[0])
            prevOpponentId = opponentId = int(r[1])

        print('player ids:', playerId, opponentId)

        global player, opponent
        player = Player(id=playerId, type="me")
        opponent = Player(id=opponentId, type="opponent")
    except:
        print('cant set players')


def setFirstPlayerId():
    global firstPlayerId
    if firstPlayerId:
        return

    try:
        global netDataSyncFilePath
        with open(netDataSyncFilePath, "r", encoding=ENCODING) as f:
            file = f.read()
            firstPlayerId = int(re.search("playerID:'(\d+)', targetName:'StartTurnCardDraw", file).groups()[0])
            print('firstPlayerId', firstPlayerId)
    except:
        print('not found firstPlayerId')


def getGameId():
    global outputLogSimpleFilePath

    with open(outputLogSimpleFilePath, "r", encoding=ENCODING) as f:
        file = f.read()
        gameId = re.search("Command line arguments confirmed.*game_id: \$([\w-]+)", file).groups()[0]

    return gameId


def processCombatRecorder():
    global firstPlayerId
    global combatRecorderFilePath

    playerIds = [player.id, opponent.id]

    if (player.id != firstPlayerId):
        playerIds = playerIds[:: -1]

    # todo: rewrite this
    cards = {
        playerIds[0]: {
            'drawnCardIds': [],
            'playedCardIds': []
        },
        playerIds[1]: {
            'drawnCardIds': [],
            'playedCardIds': []
        }
    }

    try:
        with open(combatRecorderFilePath, "r", encoding=ENCODING) as f:
            file = f.read()

            # todo: find 3 first drew card only (mulligan)
            for name in re.findall('Drew Card: (.*)$', file, re.MULTILINE)[:3]:
                # print(f'draw - {name}')
                card = py_.find(GU_DATA["records"], lambda x: x["name"] == name)

                if card:
                    cards[player.id]['drawnCardIds'].append(card["id"])

            turns = re.findall("^.*StartTurn[^#]*?EndTurn.*$", file, re.MULTILINE)

            for (index, turn) in enumerate(turns):
                currentPlayerId = playerIds[index % 2]
                # print(f"\n{'_' * ROW_LENGTH}\nturn {currentPlayerId}")
                # print(turn)

                for name in re.findall('Drew Card: (.*)$', turn, re.MULTILINE):
                    # print(f'draw - {name}')
                    card = py_.find(GU_DATA["records"], lambda x: x["name"] == name)

                    if card:
                        cards[currentPlayerId]['drawnCardIds'].append(card["id"])

                for name in re.findall('Played \| Card: (.*)$', turn, re.MULTILINE):
                    # print(f'play - {name}')
                    card = py_.find(GU_DATA["records"], lambda x: x["name"] == name)

                    if card:
                        cards[currentPlayerId]['playedCardIds'].append(card["id"])

        for playerId in playerIds:
            currentPlayer = player if player.id == playerId else opponent
            currentPlayer.deck.playedCardIds = cards[playerId]['playedCardIds']
            currentPlayer.deck.drawnCardIds = cards[playerId]['drawnCardIds']
    except:
        print('not found combat log file')

        global gameId
        currentGameId = getGameId()

        if gameId != currentGameId:
            gameId = currentGameId
            print('new game started')
            resetPlayersData()


#################
# GUI Functions #
#################

# Calls getOpponentsWebpage, but if it errors, provides an error warning to the user
def opponentsWebpage(logFolderPath):
    res = getOpponentWebpage(logFolderPath)
    if (res == -1):
        alert = QMessageBox()
        alert.setText('Opponent User ID Not Found. Please try again in a few seconds. [Debugging Code: 0201]')
        alert.exec()
    elif (res == -2):
        alert = QMessageBox()
        alert.setText('No valid log file found. Please check path. [Debugging Code: 0202]')
        alert.exec()


def toggleConfigBoolean(configFile, key):
    currVal = getConfigVal(configFile, key) == 'True'
    print('toggleConfigBoolean', key, currVal, not currVal)
    updateConfig(configFile, key, not currVal)

    if key == 'deckTracker' and not currVal:
        resetPlayersData()


# Main Window which includes the deck tracker
class MainWindow(QWidget):
    def __init__(self, windowTitle, windowIcon, configFile):
        super().__init__()

        #################
        # Initial Setup #
        #################

        # Setting all the inputs to "self.X" values so I can use it in update
        self.windowTitle = windowTitle
        self.windowIcon = windowIcon
        self.configFile = configFile

        # Find and set initial preference values
        self.textFont = getConfigVal(configFile, "textFont")
        self.textSize = int(getConfigVal(configFile, "textSize"))
        self.opacity = float(getConfigVal(configFile, "opacity"))
        self.logFolderPath = getConfigVal(configFile, "logFolderPath")

        # Always start with the deck tracker disabled, regardless of previous settings
        updateConfig(configFile, "deckTracker", False)
        self.showTracker = False

        # This is so that we don't spam the user with tons of warnings if a log file can't be found
        self.warnedAboutLogFile = False
        # This keeps track of the last log path we warned about, so we know if we should update warnedAboutLogFile
        self.warnedlogFolderPath = ""

        ###############################
        # Creation of the Main Window #
        ###############################

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.tempWindow = None
        self.layout = QVBoxLayout()
        self.setWindowTitle(windowTitle)
        self.setWindowIcon(QIcon(windowIcon))

        self.opponentPageButton = QPushButton("Open Opponent's GUDecks Page", self)

        # I wanted to call this, but you have to do the line beneath it instead for some reason:
        # self.opponentPageButton.clicked.connect(opponentsWebpage(logFolderPath))
        self.opponentPageButton.clicked.connect(lambda i: opponentsWebpage(self.logFolderPath))
        self.opponentPageButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.opponentPageButton)

        self.settingsButton = QPushButton("Settings", self)
        self.settingsButton.clicked.connect(self.settings)
        self.settingsButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.settingsButton)

        self.toggleDeckTrackerButton = QPushButton("Toggle Deck Tracker", self)
        self.toggleDeckTrackerButton.clicked.connect(lambda i: toggleConfigBoolean(self.configFile, "deckTracker"))
        self.toggleDeckTrackerButton.clicked.connect(self.update)
        self.toggleDeckTrackerButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.toggleDeckTrackerButton)

        self.deckTrackerLabel = QLabel()
        self.deckTrackerLabel.setFont(QFont(self.textFont, self.textSize))
        if (self.showTracker):
            self.layout.addWidget(self.deckTrackerLabel)

        self.setLayout(self.layout)
        self.show()

        # Update once per interval
        self.my_timer = QtCore.QTimer()
        self.my_timer.timeout.connect(self.update)
        # todo: start immediately
        # self.my_timer.start(5000)  # 5 sec
        self.my_timer.start(1000)  # 1 sec

    # Constantly looping update to keep the deck tracker up to date
    def update(self):
        ######################
        # Update Preferences #
        ######################

        print('update tick')

        # Find and set current preference values
        self.textFont = getConfigVal(configFile, "textFont")
        self.textSize = int(getConfigVal(configFile, "textSize"))
        self.opacity = float(getConfigVal(configFile, "opacity"))
        self.logFolderPath = getConfigVal(configFile, "logFolderPath")

        self.showTracker = True
        if (getConfigVal(configFile, "deckTracker") == "False"):
            self.showTracker = False

        # Update Tracker based on new settings
        self.opponentPageButton.setFont(QFont(self.textFont, self.textSize))
        self.settingsButton.setFont(QFont(self.textFont, self.textSize))
        self.toggleDeckTrackerButton.setText(f'Toggle {"off" if self.showTracker else "on"} Deck Tracker')
        self.toggleDeckTrackerButton.setFont(QFont(self.textFont, self.textSize))
        self.deckTrackerLabel.setFont(QFont(self.textFont, self.textSize))
        self.setWindowOpacity(self.opacity)

        # If we have a different path than the one we previously warned about, we have no longer warned about the
        #   current log file
        if (self.warnedlogFolderPath != self.logFolderPath):
            self.warnedAboutLogFile = False

        ########################
        # Update the deck list #
        ########################

        decksText = ''

        if self.showTracker:
            setPlayers()

            if not playerId or not opponentId:
                return

            if not player.hasDeckList:
                print('not found my deck')
                startingCardIds = getStartingCardIds()
                player.deck.setDeckList('unknown', startingCardIds)

            if not opponent.hasDeckList:
                print('not found opponent deck')
                (god, cardIds, archetype, stats) = getOpponentDeck()
                opponent.deck.setDeckList(god, cardIds, archetype, stats)

            setFirstPlayerId()
            processCombatRecorder()

            # if (updatedList == -1):
            #     if (self.warnedAboutLogFile):
            #         # We are already warned about the log file, so we just need the user to update the logfile
            #         return
            #     else:
            #         # We need to warn the user that the current log path isn't valid. This is extremely weird, though,
            #         #   since we've made it past startingDeckList. If this happens, there was probably a restructuring
            #         #   of the logs files, which would suck.
            #         alert = QMessageBox()
            #         alert.setText('No valid log file found. Please check path. [Debugging Code: 0102]')
            #         alert.exec()
            #         self.warnedAboutLogFile = True
            #         self.warnedlogFolderPath = self.logFolderPath
            #         return
            # elif (updatedList == -2):
            #     # Event solver doesn't exist yet, so just wait
            #     return

            decksText = getDecksStr()

        self.deckTrackerLabel.setText(decksText)

        if (self.showTracker):
            self.layout.addWidget(self.deckTrackerLabel)
        else:
            self.layout.removeWidget(self.deckTrackerLabel)

        # self.setLayout(self.layout)
        self.adjustSize()

    def settings(self):
        self.tempWindow = SettingsWindow(self.windowTitle, self.configFile)


class SettingsWindow(QWidget):
    def __init__(self, windowTitle, configFile):
        super().__init__()

        # Setting all the inputs to "self.X" values so I can use it in confirm
        self.configFile = configFile

        # Find and set current preference values
        self.textFont = getConfigVal(configFile, "textFont")
        self.textSize = int(getConfigVal(configFile, "textSize"))
        self.opacity = float(getConfigVal(configFile, "opacity"))
        self.logFolderPath = getConfigVal(configFile, "logFolderPath")
        # We don't need deckTracker

        self.setWindowOpacity(self.opacity)
        self.setWindowTitle(windowTitle)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.layout = QVBoxLayout()

        self.updateNotify = True
        strToDisplay = "(Currently Enabled)"
        if (getConfigVal(self.configFile, "updateNotify") == "False"):
            self.updateNotify = False
            strToDisplay = "(Currently Disabled)"

        self.updateNotifyButton = QPushButton("Toggle Update Notifications " + strToDisplay, self)
        self.updateNotifyButton.clicked.connect(lambda i: toggleConfigBoolean(self.configFile, "updateNotify"))
        self.updateNotifyButton.clicked.connect(self.updateText)
        self.updateNotifyButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.updateNotifyButton)

        strToDisplay = "(Currently Enabled)"
        if (getConfigVal(self.configFile, "autoUpdate") == "False"):
            self.updateNotify = False
            strToDisplay = "(Currently Disabled)"

        self.autoUpdateButton = QPushButton("Toggle Automatic Updates " + strToDisplay, self)
        self.autoUpdateButton.clicked.connect(lambda i: toggleConfigBoolean(self.configFile, "autoUpdate"))
        self.autoUpdateButton.clicked.connect(self.updateText)
        self.autoUpdateButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.autoUpdateButton)

        self.textSizeLabel = QLabel("Enter desired text size (Currently " + str(self.textSize) + "):")
        self.textSizeLabel.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.textSizeLabel)

        self.textSizeEdit = QLineEdit("")
        self.textSizeEdit.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.textSizeEdit)

        self.textFontLabel = QLabel("Enter desired text font (Currently " + str(self.textFont) + "):")
        self.textFontLabel.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.textFontLabel)

        self.textFontEdit = QLineEdit("")
        self.textFontEdit.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.textFontEdit)

        self.opacityLabel = QLabel("Enter desired opacity (Currently " +
                                   str(self.opacity) + "; Range 0.25-1):")
        self.opacityLabel.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.opacityLabel)

        self.opacityEdit = QLineEdit("")
        self.opacityEdit.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.opacityEdit)

        self.pathLabel = QLabel("Enter path to 'FuelGames' log folder:")
        self.pathLabel.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.pathLabel)

        self.pathEdit = QLineEdit("")
        self.pathEdit.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.pathEdit)

        self.confirmButton = QPushButton("Apply", self)
        self.confirmButton.clicked.connect(self.confirm)
        self.confirmButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.confirmButton)

        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(self.cancel)
        self.cancelButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.cancelButton)

        self.setLayout(self.layout)
        self.show()

    def updateText(self):
        self.updateNotify = True
        strToDisplay = "(Currently Enabled)"
        if (getConfigVal(self.configFile, "updateNotify") == "False"):
            self.updateNotify = False
            strToDisplay = "(Currently Disabled)"

        self.updateNotifyButton.setText("Toggle Update Notifications " + strToDisplay)

        strToDisplay = "(Currently Enabled)"
        if (getConfigVal(self.configFile, "autoUpdate") == "False"):
            self.updateNotify = False
            strToDisplay = "(Currently Disabled)"

        self.autoUpdateButton.setText("Toggle Automatic Updates " + strToDisplay)

    def confirm(self):
        # 0 (Text Font)
        if (not str(self.textFontEdit.text()) == ""):
            updateTextFont = self.textFontEdit.text()
            updateConfig(self.configFile, "textFont", updateTextFont)

        # 1 (Text Size)
        if (not str(self.textSizeEdit.text()) == ""):
            if (str(self.textSizeEdit.text()).isdigit()):
                updateTextSize = int(self.textSizeEdit.text())

                if (updateTextSize < 5):
                    updateTextSize = 5
                elif (updateTextSize > 80):
                    updateTextSize = 80

                updateConfig(self.configFile, "textSize", updateTextSize)

        # 2 (Opacity)
        if (not str(self.opacityEdit.text()) == ""):

            if (str(self.opacityEdit.text()).replace(".", "", 1).isdigit() and
                    str(self.opacityEdit.text()).count(".") < 2):

                updateOpacity = float(self.opacityEdit.text())
                if (updateOpacity < 0.25):
                    updateOpacity = 0.25
                elif (updateOpacity > 1):
                    updateOpacity = 1
                updateConfig(self.configFile, "opacity", updateOpacity)

        # 3 (logFile)
        if (not str(self.pathEdit.text()) == ""):
            updateLogPath = str(self.pathEdit.text())

            if (not os.path.exists(updateLogPath)):
                alert = QMessageBox()
                alert.setText('Warning: Path not found. Please enter a valid path.')
                alert.exec()

            else:
                subDirs = [(updateLogPath + "\\" + d) for d in os.listdir(updateLogPath)
                           if os.path.isdir((updateLogPath + "\\" + d))]
                updateLogPath = max(subDirs, key=os.path.getmtime)
                updateConfig(self.configFile, "logFolderPath", updateLogPath)

        self.close()

    def cancel(self):
        self.close()


##########################
# Auto-Updater Functions #
##########################

# Compares two versions of the format X-Y-Z; numbers with hyphens in between
# If v1 > v2, return 1 (This shouldn't happen usually)
# If v1 == v2, return 0
# If v1 < v2, return -1
def compareVersions(v1, v2):
    splitV1 = v1.split("-")
    splitV2 = v2.split("-")

    # Which one is longer matters if the shorter one equals the longer one all the way to the end; if that's the case
    #   then the longer one is greater
    v1Longer = (len(splitV1) > len(splitV2))

    minLength = len(splitV1)
    maxLength = len(splitV2)
    if (v1Longer):
        minLength = len(splitV2)
    else:
        maxLength = len(splitV2)

    for n in range(minLength):
        if (int(splitV1[n]) > int(splitV2[n])):
            return 1
        elif (int(splitV1[n]) < int(splitV2[n])):
            return -1

    # At this point, we have a tie
    if (minLength == maxLength):
        return 0
    elif (minLength == len(splitV1)):
        return -1
    else:
        return 1


def findGithubVersion():
    githubData = urllib.request.urlopen("https://github.com/antofa/GU_Deck_Tracker/")
    githubString = githubData.read().decode("utf8")
    return re.search('gu_tracker-v(.*).py" ', githubString).group(1).strip()


def openPatchNotesWebpage():
    webbrowser.open(("https://github.com/antofa/GU_Deck_Tracker/blob/main/ChangeLog.md"), new=2, autoraise=True)


def updateAndRestart(configFile, updateVersion):

    # We are updating, so set justUpdated to True
    updateConfig(configFile, "justUpdated", "True")

    # Delete this file (Doesn't work; no permissions.)
    # os.chmod(sys.argv[0], 0o777)
    # os.remove(sys.argv[0])

    # subprocess.Popen("python -c \"import os, time; time.sleep(1); os.remove(r'{}');\"".format(sys.argv[0]), shell=True)

    # Download the .exe
    filename, headers = urllib.request.urlretrieve(
        "https://github.com/antofa/GU_Deck_Tracker/releases/download/" + updateVersion +
        "/gu_tracker-v" + updateVersion + ".exe", "gu_tracker-v" + updateVersion + ".exe")

    # If people want to auto update with the .py file, uncomment this out

    # Download the .py
    # urllib.request.urlretrieve(
    #    "https://github.com/antofa/GU_Deck_Tracker/releases/download/" + updateVersion + "/gu_tracker-v" +
    #    updateVersion + ".py", "gu_tracker-v" + updateVersion + ".py")
    #
    # Download the condensed_card_library.txt
    # urllib.request.urlretrieve(
    #    "https://github.com/antofa/GU_Deck_Tracker/releases/download/" + updateVersion +
    #    "/condensed_card_library.txt", "condensed_card_library.txt")

    # Run the new version of the tracker and end this one
    subprocess.Popen(filename)
    sys.exit()


class JustUpdatedWindow(QWidget):
    def __init__(self, configFile, updateVersion):
        super().__init__()

        self.textFont = getConfigVal(configFile, "textFont")
        self.textSize = int(getConfigVal(configFile, "textSize"))
        self.opacity = float(getConfigVal(configFile, "opacity"))

        self.setWindowOpacity(self.opacity)
        self.setWindowTitle("Just Updated!")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.layout = QVBoxLayout()

        self.displayText = QLabel("You have just updated to version " + updateVersion + "!")
        self.displayText.setFont(QFont(self.textFont, self.textSize))
        self.displayText.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.displayText)

        self.openPage = QPushButton("View Patch Notes", self)
        self.openPage.clicked.connect(openPatchNotesWebpage)
        self.openPage.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.openPage)

        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.closeButton)

        self.setLayout(self.layout)
        self.show()


class UpdateWindow(QWidget):
    def __init__(self, configFile, updateVersion):
        super().__init__()

        self.textFont = getConfigVal(configFile, "textFont")
        self.textSize = int(getConfigVal(configFile, "textSize"))
        self.opacity = float(getConfigVal(configFile, "opacity"))

        self.setWindowOpacity(self.opacity)
        self.setWindowTitle("Update Available!")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.layout = QVBoxLayout()

        self.updateAvailableText = QLabel("Version " + updateVersion + " is available now!\n\nYou can toggle " +
                                          "auto-updates and update notifications in the settings.")
        self.updateAvailableText.setFont(QFont(self.textFont, self.textSize))
        self.updateAvailableText.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.updateAvailableText)

        self.openPage = QPushButton("View Patch Notes", self)
        self.openPage.clicked.connect(openPatchNotesWebpage)
        self.openPage.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.openPage)

        self.updateNow = QPushButton("Update Now! (Will freeze for a little; don't worry!)", self)
        self.updateNow.clicked.connect(lambda i: updateAndRestart(configFile, updateVersion))
        self.updateNow.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.updateNow)

        self.closeButton = QPushButton("Continue without updating", self)
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setFont(QFont(self.textFont, self.textSize))
        self.layout.addWidget(self.closeButton)

        self.setLayout(self.layout)
        self.show()


def showJustUpdatedWindow(configFile, updateVersion):
    updateApp = QApplication([])
    updateApp.setStyle('Fusion')

    justUpdatedWindow = JustUpdatedWindow(configFile, updateVersion)

    # At this point we know we want to notify but not autoupdate

    # This is stolen from: https://stackoverflow.com/questions/48256772/dark-theme-for-qt-widgets
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    updateApp.setPalette(palette)

    # If notifications are off, don't message
    # Also, if autoUpdate is on then we don't need this window since we're updating anyway
    updateApp.exec()

    return justUpdatedWindow


def updateTracker(configFile, updateVersion):
    notify = True
    if (getConfigVal(configFile, "updateNotify") == "False"):
        notify = False

    autoUpdate = True
    if (getConfigVal(configFile, "autoUpdate") == "False"):
        autoUpdate = False

    # If auto updates are enabled, just update
    if (autoUpdate):
        updateAndRestart(configFile, updateVersion)
        return

    # If we don't want to be notified, then don't show this
    elif (not notify):
        return

    updateApp = QApplication([])
    updateApp.setStyle('Fusion')

    updateWindow = UpdateWindow(configFile, updateVersion)

    # At this point we know we want to notify but not autoupdate

    # This is stolen from: https://stackoverflow.com/questions/48256772/dark-theme-for-qt-widgets
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    updateApp.setPalette(palette)

    # If notifications are off, don't message
    # Also, if autoUpdate is on then we don't need this window since we're updating anyway
    updateApp.exec()

    return updateWindow


if __name__ == "__main__":
    # retrive game id at start
    gameId = getGameId()

    # defaults
    defaultFont = "Helvetica"
    defaultSize = 14
    defaultOpacity = 1

    # File Paths
    configFile = "config.txt"

    #####################
    # Check for updates #
    #####################

    gitHubVersion = 0  # findGithubVersion()
    # versionComparison = compareVersions(gitHubVersion, localVersion)
    # skip version check for now
    versionComparison = 0

    keepReference = None

    # This means we have a new update!
    if (versionComparison > 0):
        keepReference = updateTracker(configFile, gitHubVersion)

    windowTitle = f'GU Deck Tracker {localVersion}'
    windowIcon = './media/logo.ico'

    # Check to see if we haven't run this since updating it
    if (getConfigVal(configFile, "justUpdated") == "True"):
        justUpdatedWindow = showJustUpdatedWindow(configFile, localVersion)

    # After we've checked for updates, we know that we are no longer running this version for the first time
    #   (because when we update, we force a restart)
    updateConfig(configFile, "justUpdated", "False")

    app = QApplication([])
    app.setStyle('Fusion')

    mainWindow = MainWindow(windowTitle, windowIcon, configFile)

    # This is stolen from: https://stackoverflow.com/questions/48256772/dark-theme-for-qt-widgets
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    app.exec()
