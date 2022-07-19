# -*- coding: utf8 -*-
import pydash as py_
from pprint import pprint, pformat
from copy import deepcopy

from utils.globals import GU_DATA

INDEX_ID = 0
INDEX_NAME = 1
INDEX_MANA = 2
INDEX_TYPE = 3
INDEX_RARITY = 4
INDEX_COUNT = 5
NAME_LENGTH = 20
ROW_LENGTH = NAME_LENGTH + 9
TEXT_MODE = False

CARD_TYPE_CHARS = {
    'crystal': '♦',
    'weapon': '🔪',
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

CARD_UNKNOWN = {
    "id": -1,
    "name": "unknown",
    "mana": 0,
    "type": "unknown"
}


def getCardTypeChar(cardType):
    return py_.get(CARD_TYPE_CHARS, cardType, CARD_TYPE_CHARS["unknown"])


def findCard(**kwargs):
    cardId = py_.get(kwargs, 'id')
    name = py_.get(kwargs, 'name')
    artId = py_.get(kwargs, 'artId')
    return py_.find(GU_DATA['records'], lambda x: x['id'] == cardId or x['name'] == name or x['art_id'] == artId) or CARD_UNKNOWN


class Deck(object):
    def __init__(self, **kwargs):
        [god, *cardIds] = py_.get(kwargs, 'deckCode', '').split(',')
        self.player = py_.get(kwargs, 'player')
        self.god = 'unknown'
        self.archetype = 'unknown'
        self.stats = {}
        self.deckCardIds = []
        self.deckList = []
        self.playedCardIds = []
        self.drawnCardIds = []

        self.setDeckList(god, cardIds)

    def __str__(self):
        title = f'{self.archetype}'
        subtitle = ''

        if (self.stats):
            winrate = self.stats['userWins'] / (self.stats['userWins'] + self.stats['userLosses']) * 100
            subtitle = f' {self.stats["userWins"]}W / {self.stats["userLosses"]}L {winrate: .1f}%'

        spacer = '_' * ROW_LENGTH
        textBlocks = [f'{title[:NAME_LENGTH]: ^{ROW_LENGTH}}' + '\n' + f'{subtitle[:NAME_LENGTH]: ^{ROW_LENGTH}}']

        if self.player == 'me':
            textBlocks.extend([self.getCardListStr('notDrawnList'),
                               self.getCardListStr('playedList')])
        else:
            textBlocks.extend([self.getCardListStr('notPlayedList'),
                               self.getCardListStr('playedList')])

        return f'\n{spacer}\n'.join(x for x in textBlocks)

    def asHtml(self):
        title = f'{self.archetype}'
        subtitle = ''

        if (self.stats):
            winrate = self.stats['userWins'] / (self.stats['userWins'] + self.stats['userLosses']) * 100
            subtitle = f' {self.stats["userWins"]}W / {self.stats["userLosses"]}L {winrate: .1f}%'

        spacer = '_' * ROW_LENGTH
        blocks = [f'''<div><span>{title[:NAME_LENGTH]: ^{ROW_LENGTH}}</span><span>{subtitle[:NAME_LENGTH]: ^{ROW_LENGTH}}</span></div>''']

        if self.player == 'me':
            blocks.extend([self.getCardListHtml('notDrawnList'),
                           self.getCardListHtml('playedList')])
        else:
            blocks.extend([self.getCardListHtml('notPlayedList'),
                           self.getCardListHtml('playedList')])

        return f'\n'.join(x for x in blocks)

    def getCardListStr(self, listKey='deckList'):
        cardsList = py_.get(self, listKey)
        rows = []
        for card in cardsList:
            [_, name, mana, cardType, rarity, amount] = card
            rows.append(f'{mana}{getCardTypeChar("crystal")} {getCardTypeChar(cardType)} {name[:NAME_LENGTH]: <{NAME_LENGTH}} x{amount}')

        return "\n".join(rows)

    def getCardListHtml(self, listKey='deckList'):
        cardsList = py_.get(self, listKey)
        rows = []
        for card in cardsList:
            [cardId, name, mana, cardType, rarity, amount] = card
            rows.append(f'''
<div class="deck-list-item-wrapper tooltip tooltip-{'left' if self.god == 'unknown' else 'right'}">
  <div class="deck-list-item">
     <div class="deck-list-item-name-area">
        <div class="deck-list-item-name-border">
           <div class="deck-list-item-background" style="background-image: url(&quot;https://images.godsunchained.com/art2/250/{cardId}.jpg&quot;);"></div>
           <div class="deck-list-item-background-fade"></div>
           <div class="deck-list-item-background-fade-right"></div>
           <div class="deck-list-item-rarity-strip {rarity}-background"></div>
           <div class="deck-list-item-name">{mana}{getCardTypeChar("crystal")} {getCardTypeChar(cardType)} {name}</div>
           <div class="deck-list-item-count {amount <= 1 and "hidden"}">x{amount}</div>
        </div>
     </div>
  </div>
  <img src="https://card.godsunchained.com/?id={cardId}&q=5" />
</div>
            ''')

        return f'<div id="deck-list">{"".join(rows)}</div>'

    def getDeckList(self, cardIds, excludeIds=[]):
        excludeIds = deepcopy(excludeIds)
        deckList = []
        count = 1

        for cardId in cardIds:
            cardId = int(cardId)

            if cardId in excludeIds:
                excludeIds.pop(excludeIds.index(cardId))
                continue

            card = findCard(id=cardId)

            cardIndex = py_.find_index(deckList, lambda x: x[INDEX_ID] == card["id"])
            if cardIndex != -1:
                deckList[cardIndex][INDEX_COUNT] += 1
            else:
                deckList.append([card["id"], card["name"], card["mana"], card["type"], card["rarity"], count])

        # sort decklist first by mana cost, then alphabetically
        deckList = py_.order_by(deckList, [INDEX_MANA, INDEX_NAME], [True, True])

        return deckList

    def setDeckList(self, god, cardIds, archetype='unknown', stats={}):
        self.god = god
        self.deckList = self.getDeckList(cardIds)
        # save actual found card ids
        self.deckCardIds = py_.reduce_(self.deckList, lambda memo, x: memo + [x[INDEX_ID]] * x[INDEX_COUNT], [])
        self.archetype = archetype
        self.stats = stats

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
