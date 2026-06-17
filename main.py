import fastapi
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from typing import Optional

from gamemanager import GameManager
from nonogram.nonogram import Nonogram
import random

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

manager = GameManager()


@app.get("/")
def read_root(request: fastapi.Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})


@app.get("/game")
def game_page(request: fastapi.Request):
    return templates.TemplateResponse(request=request, name="game.html", context={"request": request})


@app.get("/check_solvable")
def check_solvable_get(request: fastapi.Request):
    return templates.TemplateResponse(request=request, name="check_solvable.html", context={"request": request})


@app.post("/check_solvable")
def check_solvable_post(
    rows: int,
    cols: int,
    density: float,
    random_function: str,
    frequency: int,
    seed: str,
):
    if seed.isdecimal():
        seed = int(seed)
    else:
        seed = hash(seed) % (2**16)

    nonogram = Nonogram()
    nonogram.generate_board(
        rows=rows,
        cols=cols,
        seed=seed,
        density=density,
        random_function=random_function,
        frequency=frequency,
    )
    return {"solvable": nonogram.solvable}


@app.post("/check_solvable_by_game_id")
def check_solvable_by_game_id(game_id: str):
    session = manager.get_game(game_id)
    if not session:
        return {"error": "Game not found"}
    return {"solvable": session.game_data.solvable}


@app.get("/new")
def create_new_nonogram(
    rows: int = 15,
    cols: int = 15,
    density: float = 0.5,
    random_function: str = "perlin2d",
    frequency: int = 6,
    seed: Optional[str] = None,
):
    if seed in (None, "", "undefined", "NaN", "null"):
        seed = random.randint(0, 2**16 - 1)
    elif seed.isdecimal():
        seed = int(seed)
    else:
        seed = hash(seed) % (2**16)

    nonogram = Nonogram()
    nonogram.generate_board(
        rows=rows,
        cols=cols,
        seed=seed,
        density=density,
        random_function=random_function,
        frequency=frequency,
    )
    game_id, session = manager.create_game(nonogram)
    return {"game_id": game_id,
            "width": cols,
            "height": rows,
            "hints": session.game_data.hints,
            "details": {
                "seed": seed,
                "density": density,
                "random_function": random_function,
                "frequency": frequency,
            }}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: fastapi.WebSocket, game_id: str):
    await websocket.accept()
    session = manager.get_game(game_id)
    if not session:
        await websocket.send_json({"error": "Game not found"})
        await websocket.close()
        return

    session.connections.add(websocket)
    game = session.game_data

    while True:
        try:
            data = await websocket.receive_json()
            # defining data types:
            # everything will be a dict like {"type": ..., "payload": {...}}
            if data["type"] == "update":
                # value is 0 for white 1 for black -1 for cross
                x = data["payload"]["x"]
                y = data["payload"]["y"]
                value = data["payload"]["value"]
                if 0 <= x < game.details['cols'] and 0 <= y < game.details['rows']:
                    # do better sanitization here later
                    game.move(x, y, value)
                    await session.broadcast({"type": "update",
                                             "payload": {"state": game.state,
                                                         "height": game.details['rows'],
                                                         "width": game.details['cols'],
                                                         "hints": game.hints,
                                                         "details": game.details,
                                                         "solved": game.solved}})
            elif data["type"] == "get_state":
                await websocket.send_json({"type": "state",
                                           "payload": {"state": game.state,
                                                       "height": game.details['rows'],
                                                       "width": game.details['cols'],
                                                       "hints": game.hints,
                                                       "details": game.details,
                                                       "solved": game.solved}})
            elif data["type"] == "reset":  # for later
                game.state = [[0 for x in range(game.details['cols'])] for y in range(game.details['rows'])]
                await websocket.send_json({"type": "reset", "payload": {"state": game.state}})
            elif data["type"] == "delete":
                manager.delete_game(game_id)
                await websocket.send_json({"type": "delete", "payload": {"message": "Game deleted"}})
                await websocket.close()
                session.connections.discard(websocket)
                return
            elif data["type"] == "ping":  # debug
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"error": "Unknown message type"})
            await websocket.send_json({"received": data})
        except Exception as e:
            print(f"WebSocket error: {e}")
            session.connections.discard(websocket)
            return
