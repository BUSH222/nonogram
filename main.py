import fastapi
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from nonogram.nonogram import Nonogram
import random

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def read_root(request: fastapi.Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})


@app.get("/new")
def create_new_nonogram(rows: int = 15, cols: int = 15, density: float = 0.5,
                        random_function: str = 'perlin2d', frequency: int = 6):
    seed = random.randint(0, 1000000)
    nonogram = Nonogram()
    nonogram.generate_board(rows=rows, cols=cols, seed=seed, density=density,
                            random_function=random_function, frequency=frequency)
    return nonogram.get_board()
