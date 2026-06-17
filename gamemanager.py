from uuid import uuid4
from nonogram.nonogram import Nonogram


class GameManager:
    def __init__(self):
        self.games = {}

    def create_game(self, game_data: Nonogram):
        game_id = str(uuid4())
        self.games[game_id] = game_data
        return game_id, game_data

    def get_game(self, game_id):
        return self.games.get(game_id)

    def delete_game(self, game_id):
        if game_id in self.games:
            del self.games[game_id]
            return True
        return False
