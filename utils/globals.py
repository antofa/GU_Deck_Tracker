import json

#########################
# Global variables      #
#########################

# https://images.godsunchained.com/art2/250/1446.jpg
# https://api.godsunchained.com/v0/proto?page=1&perPage=10000
GU_DATA = json.load(open("./data/data.json", "r"))
ENCODING = 'utf8'
GU_DECKS_PLAYER_PAGE_BASE = "https://gudecks.com/meta/player-stats?userId="
