# -*- coding: utf8 -*-
import pydash as py_

from utils.deck import Deck

HTML_TEMPLATE = '''
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home page</title>
    <style type="text/css">
body {
    background-color: #1d1d1d;
}

.hidden {
    display: none;
}


.common, .common:hover{
    color: #e6e6e6;
}
.common-background{
    background-color: #e6e6e6;
}
.common-word-color, .common-word-color:hover{
    color: #bdb988;
}
.rare, .rare:hover{
    color: #42a5f5;
}
.rare-background{
    background-color: #42a5f5;
}
.epic, .epic:hover{
    color: #ba68c8;
}
.epic-background{
    background-color: #ba68c8;
}
.legendary, .legendary:hover{
    color: #ffca28;
}
.legendary-background{
    background-color: #ffca28;
}
.mythic, .mythic:hover{
    color: #ef5350
}
.mythic-background{
    background-color: #ef5350
}


#deck-list-god-image-area{
    display: inline-block;
    margin-top: 10px;
    width: 240px;
    height: 50px;
    background-position: 0% -80%;
    background-size: cover;
    border: 3px solid #505050;
    border-radius: 6px;
}

#deck-list{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: Consolas;
}

.deck-list-item-wrapper{
 display: flex;
 align-items: center;
}

.deck-list-item-wrapper:not(:last-child){
    margin-bottom: 2px;
}

.deck-list-item{
    display : flex;
    justify-content: center;
    align-items: center;
    color:white;
    font-size: 1.3em;
    cursor: pointer;
    width: fit-content;
}
.deck-list-item-unowned{
    opacity: .5;
}

.deck-list-item:hover {
    filter: brightness(1.2);
}

.deck-list-item-name-border{
    display: flex;
    font-size: .7em;
    width: 250px;
    border: 1px solid rgb(80, 80, 80);
    position: relative;
    padding: 5px;
}
.god-power-list-item-name-border{
    width: 10.5em;
    border: 2px solid rgb(185, 161, 94);
    position: relative;
    padding: 0 0 0 1.3em;
    border-radius: 6px;
}
.deck-list-item-background{
    position: absolute;
    background-size: cover;
    background-position-y: 20%;
    opacity: .9;
    top: 0;
    left: 45%;
    bottom: 0;
    right: 5%;
    z-index: 0;
}
.deck-list-item-background-unowned{
    filter:saturate(.5);
}

.deck-list-item-background-fade{
    position: absolute;
    background-image: linear-gradient(to right, #1d1d1d, #1d1d1d00);
    top: 0;
    left: 45%;
    bottom: 0;
    right: 30%;
    z-index: 0;
}
.deck-list-item-background-fade-right{
    position: absolute;
    background-image: linear-gradient(to right, #1d1d1d00, #1d1d1d);
    top: 0;
    left: 78%;
    bottom: 0;
    right: 4.5%;
    z-index: 0;
}
.deck-list-item-name{
    text-overflow: ellipsis;
    /* required for ellipsis */
    overflow: hidden;
    white-space: nowrap;
    text-align: left;
    flex-grow: 1;
    z-index: 1;
}
.deck-list-item-count{
    margin-right: 15px;
    z-index: 1;
}
.deck-list-item-rarity-strip{
    position: absolute;
    top: 0;
    left: 98%;
    bottom: 0;
    right: 0;
    z-index: 0;
}

.deck-list-item-percentage{
  margin-left: 10px;
  color:darkgrey;
 }



div.tooltip img {
  z-index:10;
  display:none;
  margin-top:5px;
  background: gray;
}
div.tooltip:hover img{
    display:inline; position:absolute; 
    left: 5px;
    background: transparent;
}
    </style>
</head>
<body>

[DECKS]
</body>
</html>
'''


class Player(object):
    # type - me, opponent
    def __init__(self, **kwargs):
        self.id = py_.get(kwargs, 'id')
        self.type = py_.get(kwargs, 'type', 'me')
        self.deck = Deck(deckCode=py_.get(kwargs, 'deckCode', ''), player=self.type)

    def __str__(self):
        return f'Player ({self.type})\n{self.deck}'

    def asHtml(self):
        return HTML_TEMPLATE.replace('[DECKS]', self.deck.asHtml())

    @property
    def hasDeckList(self):
        return not self.deck.isEmptyDeck
