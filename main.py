import json
import random
import zlib
from pathlib import Path
from typing import Any

import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gamemanager import GameManager
from nonogram.nonogram import Nonogram

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

manager = GameManager()


def load_seedbank(directory: Path) -> dict[tuple[int, int], dict[str, Any]]:
    """Load the solvable seeds written by build_seedbank.py, keyed by (rows, cols)."""
    bank = {}
    for path in directory.glob("*.json"):
        data = json.loads(path.read_text())
        bank[(data["rows"], data["cols"])] = data
    return bank


seedbank = load_seedbank(Path("seedbank"))


def seed_to_int(seed: str) -> int:
    # crc32 rather than hash(): str hashes are randomized per process, so the same text seed
    # would give a different puzzle after every server restart.
    return int(seed) if seed.isdecimal() else zlib.crc32(seed.encode()) % (2**16)


@app.get("/")
def read_root(request: fastapi.Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "seedbank_sizes": sorted(seedbank)},
    )


@app.get("/seedbank/random")
def seedbank_random(rows: int, cols: int):
    """A random solvable seed for this size, with the settings it must be generated with."""
    bank = seedbank.get((rows, cols))
    if bank is None:
        raise HTTPException(status_code=404, detail=f"No seed bank for {rows}x{cols}")
    seed, difficulty = random.choice(bank["seeds"])
    return {
        "seed": seed,
        "difficulty": difficulty,
        "density": bank["density"],
        "random_function": bank["random_function"],
        "frequency": bank["frequency"],
    }


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
    seed_int = seed_to_int(seed)

    nonogram = Nonogram()
    nonogram.generate_board(
        rows=rows,
        cols=cols,
        seed=seed_int,
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
    seed: str | None = None,
):
    if seed is None or seed in ("", "undefined", "NaN", "null"):
        seed_int = random.randint(0, 2**16 - 1)
    else:
        seed_int = seed_to_int(seed)

    nonogram = Nonogram()
    nonogram.generate_board(
        rows=rows,
        cols=cols,
        seed=seed_int,
        density=density,
        random_function=random_function,
        frequency=frequency,
    )
    game_id, session = manager.create_game(nonogram)
    return {
        "game_id": game_id,
        "width": cols,
        "height": rows,
        "hints": session.game_data.hints,
        "details": {
            "seed": seed_int,
            "density": density,
            "random_function": random_function,
            "frequency": frequency,
        },
    }


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
                if 0 <= x < game.details["rows"] and 0 <= y < game.details["cols"]:
                    # do better sanitization here later
                    game.move(x, y, value)
                    await session.broadcast(
                        {
                            "type": "update",
                            "payload": {
                                "state": game.state,
                                "height": game.details["rows"],
                                "width": game.details["cols"],
                                "hints": game.hints,
                                "user_highlighted_hints": game.user_highlighted_hints,
                                "details": game.details,
                                "solved": game.solved,
                            },
                        }
                    )
            elif data["type"] == "get_state":
                await websocket.send_json(
                    {
                        "type": "state",
                        "payload": {
                            "state": game.state,
                            "height": game.details["rows"],
                            "width": game.details["cols"],
                            "hints": game.hints,
                            "user_highlighted_hints": game.user_highlighted_hints,
                            "details": game.details,
                            "solved": game.solved,
                        },
                    }
                )
            elif data["type"] == "highlight_hint":
                axis = data["payload"]["axis"]
                idx = data["payload"]["idx"]
                num = data["payload"]["num"]
                assert axis in ["row", "col"]
                axis = 0 if axis == "row" else 1
                if 0 <= idx < len(game.hints[axis]) and 0 <= num < len(game.hints[axis][idx]):
                    game.user_highlighted_hints[axis][idx][num] = not game.user_highlighted_hints[axis][idx][num]
                    await session.broadcast(
                        {
                            "type": "highlight_hint",
                            "payload": {
                                "axis": axis,
                                "idx": idx,
                                "num": num,
                                "highlighted": game.user_highlighted_hints[axis][idx][num],
                            },
                        }
                    )
            elif data["type"] == "reset":  # for later
                game.state = [[0 for x in range(game.details["cols"])] for y in range(game.details["rows"])]
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
