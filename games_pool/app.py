import jwt
import logging
import os
from fastapi import FastAPI, Response, status, HTTPException, Request
from pydantic import BaseModel
import chess
import chess.pgn
from datetime import datetime, timezone
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
# import cairosvg
from typing import List
import chess.svg
import requests
import json
import jwt
from broker_db import Broker

SECRET_KEY = os.getenv("SECRET_KEY")
MY_SECRET = os.getenv("MY_SECRET")
app = FastAPI()

templates = Jinja2Templates(directory="templates")

games = {}

class ChessGame:
    def __init__(self, id: str, white_id: str, black_id: str, game_id: str, host: str, port: str, initial_time: int = 600, increment: int = 5):
        self.id = id
        self.host = host
        self.port = port
        self.board = chess.Board()
        self.pgn_game = chess.pgn.Game()
        self.pgn_node = self.pgn_game
        self.time_left = {"white": initial_time, "black": initial_time}
        self.player_id = {"white": white_id, "black": black_id}
        self.game_id = game_id
        self.increment = increment
        self.last_move_time = datetime.now()
        self.current_player = "white" # Starts
        self.pgn_text = ''
        self.result = ''
        self.winner = ''
        self.start_game = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        self.pgn_game.headers['Event'] = 'Normal Game'
        self.pgn_game.headers['White'] = white_id
        self.pgn_game.headers['Black'] = black_id
        self.pgn_game.headers['Site'] = 'Capivara Chess'

    def as_dict(self):
        return {
            'id': self.id,
            'time_left': self.time_left,
            'player_id': self.player_id,
            'result': self.result,
            'winner': self.winner,
        }

    def switch_player(self):
        self.current_player = "black" if self.current_player == "white" else "white"

    def already_registered(self):
        try:
            if Broker.get(f'game:{self.game_id}'):
               return True
        except Exception as e:
            logging.warning("ChessGame def already_registered(self):")
            logging.warning(e)
            raise HTTPException(status_code=500, detail="Error")

        return False

    def register_end_of_game(self, winner, result):
        if self.already_registered():
            return

        url = f"http://games_results:9001/api/v1/games/?secret={MY_SECRET}"

        payload = {
            "game_id": self.game_id,
            "player_white": self.player_id['white'],
            "player_black": self.player_id['black'],
            "player_winner": self.player_id[winner] if winner != None else '00000000-0000-0000-0000-000000000000',
            "start_time": self.start_game,
            "end_time": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "result": result,
            'pgn_text': self.pgn_text
        }

        self.result = result
        self.winner = winner

        token1 = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm="HS256",
        )
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=json.dumps({'token': token1}))

        if response.status_code != 200:
            logging.warning(f'Error on save result of game. Status_code {response.status_code}. Response {response.text}. token {token1}')


    def update_time(self):
        now = datetime.now()
        elapsed = (now - self.last_move_time).total_seconds()
        self.time_left[self.current_player] -= elapsed
        if self.time_left[self.current_player] < 0:
            self.time_left[self.current_player] = 0  # Evitar valores negativos
        self.time_left[self.current_player] += self.increment
        self.last_move_time = now

    def check_game_status(self):
        """Verifica se a partida acabou e retorna o estado."""

        if self.board.is_checkmate():
            return {"status": "finished", "result": "checkmate", "winner": "black" if self.board.turn else "white", "time_left": None, "turn": None}
        elif self.board.is_stalemate():
            return {"status": "finished", "result": "stalemate", "winner": None, "time_left": None, "turn": None}
        elif self.board.is_insufficient_material():
            return {"status": "finished", "result": "insufficient material", "winner": None, "time_left": None, "turn": None}
        elif self.board.is_seventyfive_moves():
            return {"status": "finished", "result": "75-move rule", "winner": None, "time_left": None, "turn": None}
        elif self.board.is_fivefold_repetition():
            return {"status": "finished", "result": "fivefold repetition", "winner": None, "time_left": None, "turn": None}
        else:
            now = datetime.now()
            if self.current_player == 'black':
                elapsed = (now - self.last_move_time).total_seconds()
                black = self.time_left['black'] - elapsed
                if black < 0:
                    black = 0

                white = self.time_left['white']
            else:
                elapsed = (now - self.last_move_time).total_seconds()
                white = self.time_left['white'] - elapsed
                if white < 0:
                    white = 0

                black = self.time_left['black']

            if black <= 0 or black == self.increment:
                return {"status": "finished", "result": "run out of time", "winner": "white", "time_left": {"black": black, "white": white}, "turn": None}
            elif white <= 0 or white == self.increment:
                return {"status": "finished", "result": "run out of time", "winner": "black", "time_left": {"black": black, "white": white}, "turn": None}


            return {"status": "ongoing", "result": None, "winner": None, "time_left": {"black": black, "white": white}, "turn": self.current_player}

class Move(BaseModel):
    move: str


@app.post("/start_game", status_code=201)
def start_game(token: str, response: Response):
    """Cria uma nova partida de xadrez."""
    token1 = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"],
    )

    if not games.get(token1['game_id']):
        games[token1['game_id']] = ChessGame(token1['game_id'], token1['players'][0], token1['players'][1], token1['game_id'], token1['pool_address']['host'], token1['pool_address']['port'])
        return {'white': token1['players'][0], 'black': token1['players'][1]}

    response.status_code = status.HTTP_200_OK
    return {'white': token1['players'][0], 'black': token1['players'][1]}

# @app.post("/start_game")
# def start_game(game_id: str, white_id: str, black_id: str):
#     """Cria uma nova partida de xadrez."""
#     games[game_id] = ChessGame(white_id, black_id)
#     return {"game_id": game_id, "message": "Nova partida criada com sucesso."}


@app.post("/make_move/{game_id}")
def make_move(game_id: str, move: Move, player_id: str):
    """Faz um movimento em uma partida específica e verifica se acabou."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    game: ChessGame = games[game_id]
    board = game.board

    if game.player_id[game.current_player] != player_id:
        if game.player_id['white'] == player_id or game.player_id['black'] == player_id:
            raise HTTPException(status_code=403, detail="Não é sua vez.")

        raise HTTPException(status_code=401, detail="Player invalido.")

    try:
        # Converte SAN para UCI, se necessário
        chess_move = board.parse_san(move.move)
    except ValueError:
        raise HTTPException(status_code=400, detail="Movimento inválido no formato SAN.")

    if chess_move not in board.legal_moves:
        raise HTTPException(status_code=400, detail="Movimento ilegal.")

    game.update_time()

    if game.time_left[game.current_player] <= 0 or game.time_left[game.current_player] == game.increment:
        status = game.check_game_status()
        if status['status'] == 'finished':
            game.register_end_of_game(status['winner'], status['result'])
        return {
            "message": f"Jogador {game.current_player} perdeu por tempo!",
            "board": str(board),
            "status": "Fim de jogo"
        }

    board.push(chess_move)
    game.pgn_node = game.pgn_node.add_variation(board.peek())
    exporter = chess.pgn.StringExporter()
    game.pgn_game.accept(exporter)

    game.switch_player()

    if board.is_checkmate():
        status = "Xeque-mate! Fim de jogo."
    elif board.is_stalemate():
        status = "Empate por afogamento (Stalemate)."
    elif board.is_insufficient_material():
        status = "Empate por material insuficiente."
    elif board.is_seventyfive_moves():
        status = "Empate por regra dos 75 lances."
    elif board.is_fivefold_repetition():
        status = "Empate por repetição de posição."
    else:
        status = "Jogo em andamento."

    if status != 'Jogo em andamento':
        status = game.check_game_status()
        if status['status'] == 'finished':
            game.pgn_text = str(exporter)
            game.register_end_of_game(status['winner'], status['result'])

    return {
        "message": f"Movimento {move.move} realizado com sucesso.",
        "board": str(board),
        "status": status,
        "time_left": game.time_left,
        "turn": game.current_player,
    }


@app.get("/get_board/{game_id}")
def get_board(game_id: str):
    """Obtém o estado atual do tabuleiro."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    game: ChessGame = games[game_id]
    board = game.board
    return {"board": str(board), "pgn": str(game.pgn_text)}


@app.get("/get_legal_moves/{game_id}")
def get_legal_moves(game_id: str):
    """Obtém os movimentos legais disponíveis na partida."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    game: ChessGame = games[game_id]
    board = game.board
    legal_moves = [board.san(move) for move in board.legal_moves]
    return {"legal_moves": legal_moves}


@app.get("/board_image/{game_id}")
def get_board_image(game_id: str):
    """Gera uma imagem do status atual do tabuleiro."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    game: ChessGame = games[game_id]
    board = game.board
    board_svg = chess.svg.board(board=board)

    # board_png = cairosvg.svg2png(bytestring=board_svg)

    return Response(content=board_svg, media_type="image/svg+xml")


@app.get("/check_status/{game_id}")
def check_status(game_id: str):
    """Endpoint para verificar o status de uma partida."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    game: ChessGame = games[game_id]
    status = game.check_game_status()
    if status['status'] == 'finished':
        game.register_end_of_game(status['winner'], status['result'])
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@app.get("/board_html/{game_id}", response_class=HTMLResponse)
async def serve_html(request: Request, game_id: str):
    game: ChessGame = games[game_id]
    image_url = f"http://{game.host}:{game.port}/board_image/{game_id}"
    return templates.TemplateResponse("game_board.html", {"request": request, "image_url": image_url})


