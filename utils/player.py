# -*- coding: utf8 -*-
import pydash as py_

from utils.deck import Deck


class Player(object):
    # type - me, opponent
    def __init__(self, **kwargs):
        self.id = py_.get(kwargs, 'id')
        self.type = py_.get(kwargs, 'type', 'me')
        self.deck = Deck(deckCode=py_.get(kwargs, 'deckCode', ''), player=self.type)

    def __str__(self):
        return f'Player ({self.type})\n{self.deck}'

    @property
    def hasDeckList(self):
        return not self.deck.isEmptyDeck
