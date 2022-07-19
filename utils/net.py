# -*- coding: utf8 -*-
import pydash as py_
import requests
from pprint import pprint
import json

from utils.globals import ENCODING

MOCK_DECK_CODE = 'war,1002,1022,1024,1024,1052,1077,1077,1140,1152,1156,1172,1180,1197,1197,1206,1214,1214,1320,1320,1324,1327,1480,1484,1489,87005,87005,87027,87027,87028,87028'


def getDeckFromAPI(playerId, currentGod, useMock=False):
    if useMock:
        return MOCK_DECK_CODE

    print(f'getDeckFromApi id={playerId} god={currentGod}')

    deck = None
    archetype = 'unknown'
    stats = {}

    # check saved opponent
    with open('./data/opponent.json', "r", encoding=ENCODING) as f:
        file = f.read()
        opponent = json.loads(file)

        if py_.get(opponent, "id") == playerId and py_.get(opponent, "god") == currentGod:
            print('found opponent deck in cache', playerId)
            return (opponent["deck"], opponent["archetype"], opponent["stats"])

    try:
        matches = requests.get('https://gjhj0jayu2.execute-api.us-east-1.amazonaws.com/dev/meta/user',
                               params={"userId": playerId}, headers={'referer': 'https://gudecks.com/'}).json()

        print(f'{len(matches)} matches')

        lastMatch = py_.find(matches, lambda x: x["player_won"] == playerId and x["winner_deck"].startswith(currentGod)
                             or x["player_lost"] == playerId and x["loser_deck"].startswith(currentGod))

        print('lastMatch', lastMatch)

        prefix = 'winner' if lastMatch["player_won"] == playerId else 'loser'
        deck = py_.get(lastMatch, f'{prefix}_deck')
        archetype = py_.get(lastMatch, f'{prefix}_archetype')
        stats = getDeckStatsFromAPI(playerId, deck)

        with open('./data/opponent.json', "w") as f:
            f.write(json.dumps({"id": playerId, "god": currentGod, "deck": deck, "archetype": archetype, "stats": stats}))
    except Exception as ex:
        print('cant get opponent deck')
        print(ex)

        # return deck of 1 rat
        deck = f'{currentGod},100071'

    return (deck, archetype, stats)


def getDeckStatsFromAPI(playerId, deck):
    stats = {}

    try:
        stats = requests.get('https://gjhj0jayu2.execute-api.us-east-1.amazonaws.com/dev/meta/matches',
                             params={"user": playerId, "deckstring": deck, 'condensed': True},
                             headers={'referer': 'https://gudecks.com/', 'x-api-key': 'eUjGoNZoXireyTFOURhh5R0pbepXgoP7kwhINhh6'}
                             ).json()[0]
    except Exception as ex:
        print('cant get opponent deck stats')
        print(ex)

    return stats


def getPlayerIdFromLatestMatches(username):
    print(f'get player id from latest matches username={username}')
    playerId = None

    try:
        matches = requests.get('https://gjhj0jayu2.execute-api.us-east-1.amazonaws.com/dev/meta/matches',
                               params={"username": username},
                               headers={'referer': 'https://gudecks.com/', 'x-api-key': 'eUjGoNZoXireyTFOURhh5R0pbepXgoP7kwhINhh6'}
                               ).json()

        print(f'{len(matches)} matches')
        print(matches)
        exit()

        lastMatch = py_.find(matches, lambda x: x["player_won_name"] == username
                             or x["player_lost_name"] == username)

        print('lastMatch', lastMatch)

        prefix = 'won' if lastMatch["player_won_name"] == username else 'lost'
        playerId = py_.get(lastMatch, f'player_{prefix}')
    except Exception as ex:
        print('cant find opponent id')
        print(ex)

    return playerId


if __name__ == "__main__":
    pass
    # (deck, archetype, stats) = getDeckFromAPI(2506619, 'nature')
    # print(deck, archetype, stats)

    getPlayerIdFromLatestMatches("Vladik734")
