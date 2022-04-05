# -*- coding: utf8 -*-
import pydash as py_
import requests
from pprint import pprint
import json

from globals import ENCODING

MOCK_DECK_CODE = 'war,1002,1022,1024,1024,1052,1077,1077,1140,1152,1156,1172,1180,1197,1197,1206,1214,1214,1320,1320,1324,1327,1480,1484,1489,87005,87005,87027,87027,87028,87028'


def getDeckFromAPI(playerId, currentGod, useMock=False):
    if useMock:
        return MOCK_DECK_CODE

    print('getDeckFromApi', playerId, currentGod)

    deck = currentGod
    opponent = None

    # check saved opponent
    with open('./data/opponent.json', "r", encoding=ENCODING) as f:
        file = f.read()
        opponent = json.loads(file)

    if py_.get(opponent, "id") == playerId and py_.get(opponent, "god") == currentGod:
        print('get opponent deck from cache', playerId)
        return opponent["deck"]

    try:
        matches = requests.get('https://gjhj0jayu2.execute-api.us-east-1.amazonaws.com/dev/meta/user',
                               params={"userId": playerId}, headers={'referer': 'https://gudecks.com/'}).json()

        pprint(matches[0])

        lastMatch = py_.find(matches, lambda x: x["player_won"] == playerId and x["winner_deck"].startswith(currentGod)
                             or x["player_lost"] == playerId and x["loser_deck"].startswith(currentGod))

        deck = py_.get(lastMatch, 'winner_deck' if lastMatch["player_won"] == playerId else 'loser_deck')

        with open('./data/opponent.json', "w") as f:
            f.write(json.dumps({"id": playerId, "god": currentGod, "deck": deck}))
    except Exception as ex:
        print('cant get opponent deck')
        print(ex)

        # return 1 rat if cant find opponent deck
        deck += ',100071'

    return deck


if __name__ == "__main__":
    deck = getDeckFromAPI(2506619, 'nature')
    print(deck)
