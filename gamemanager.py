from uuid import uuid4
from nonogram.nonogram import Nonogram


class GameManager:
    def __init__(self):
        self.games = {}

    def create_game(self, game_data: Nonogram):
        game_id = str(uuid4())
        session = GameSession(game_data)
        self.games[game_id] = session
        return game_id, session

    def get_game(self, game_id):
        return self.games.get(game_id)

    def delete_game(self, game_id):
        if game_id in self.games:
            del self.games[game_id]
            return True
        return False


class GameSession:
    def __init__(self, game_data: Nonogram):
        self.game_data = game_data
        self.connections = set()

    async def broadcast(self, message):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)
