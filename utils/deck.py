# -*- coding: utf8 -*-
import pydash as py_
from pprint import pprint, pformat
from copy import deepcopy

from utils.globals import GU_DATA

INDEX_ID = 0
INDEX_NAME = 1
INDEX_MANA = 2
INDEX_TYPE = 3
INDEX_COUNT = 4
NAME_LENGTH = 20
ROW_LENGTH = NAME_LENGTH + 9
TEXT_MODE = False

CARD_TYPE_CHARS = {
    'crystal': '♦',
    'weapon': '⚔',
    'creature': '🐼',
    'spell': '📜',
    'unknown': '💳'
} if not TEXT_MODE else {
    'crystal': 'm',
    'weapon': 'w',
    'creature': 'c',
    'spell': 's',
    'unknown': 'u'
}


def getCardTypeChar(cardType):
    return py_.get(CARD_TYPE_CHARS, cardType, CARD_TYPE_CHARS["unknown"])


class Deck(object):
    def __init__(self, **kwargs):
        [god, *cardIds] = py_.get(kwargs, 'deckCode', '').split(',')
        self.player = py_.get(kwargs, 'player')
        self.god = 'unknown'
        self.archetype = 'unknown'
        self.deckCardIds = []
        self.deckList = []
        self.playedCardIds = []
        self.drawnCardIds = []

        self.setDeckList(god, cardIds)

    def __str__(self):
        title = f'{self.god} {self.player} [{self.archetype}]'
        spacer = '_' * ROW_LENGTH
        textBlocks = [f'{title: ^{ROW_LENGTH}}']

        # print('__str__', self.player, self.deckCardIds, self.playedCardIds)

        if self.player == 'me':
            textBlocks.extend([self.getCardListStr('notDrawnList'),
                               self.getCardListStr('playedList')])
        else:
            textBlocks.extend([self.getCardListStr('notPlayedList'),
                               self.getCardListStr('playedList')])

        return f'\n{spacer}\n'.join(x for x in textBlocks)

    def getCardListStr(self, listKey='deckList'):
        cardsList = py_.get(self, listKey)
        rows = []
        for card in cardsList:
            [_, name, mana, cardType, amount] = card
            rows.append(f'{mana}{getCardTypeChar("crystal")} {getCardTypeChar(cardType)} {name[:NAME_LENGTH]: <{NAME_LENGTH}} x{amount}')

        return "\n".join(rows)

    def getDeckList(self, cardIds, excludeIds=[]):
        excludeIds = deepcopy(excludeIds)
        deckList = []
        count = 1

        for cardId in cardIds:
            cardId = int(cardId)

            if cardId in excludeIds:
                excludeIds.pop(excludeIds.index(cardId))
                continue

            card = py_.find(GU_DATA["records"], lambda x: x["id"] == cardId)

            cardIndex = py_.find_index(deckList, lambda x: x[INDEX_NAME] == card["name"])
            if cardIndex != -1:
                deckList[cardIndex][INDEX_COUNT] += 1
            else:
                deckList.append([card["id"], card["name"], card["mana"], card["type"], count])

        # sort decklist first by mana cost, then alphabetically
        deckList = py_.order_by(deckList, [INDEX_MANA, INDEX_NAME], [True, True])

        return deckList

    def setDeckList(self, god, cardIds):
        self.god = god
        self.deckCardIds = cardIds
        self.deckList = self.getDeckList(cardIds)

    @property
    def isEmptyDeck(self):
        return not self.deckList

    @property
    def playedList(self):
        return self.getDeckList(self.playedCardIds)

    @property
    def notDrawnList(self):
        return self.getDeckList(self.deckCardIds, self.drawnCardIds)

    @property
    def notPlayedList(self):
        return self.getDeckList(self.deckCardIds, self.playedCardIds)
