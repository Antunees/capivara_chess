import json
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Tuple
from uuid import uuid4
import jwt
import asyncio
import hashlib

from broker_db import Broker

SECRET_KEY = os.getenv("SECRET_KEY")
app = FastAPI()

# Fila de jogadores
global queue
queue: List[Tuple[str, WebSocket]] = []

# Lobbies ativos
active_lobbies: Dict[str, Tuple[str, str]] = {}


async def create_match():
    """
    Cria uma partida para dois jogadores da fila.
    """
    while True:
        if len(queue) >= 2:
            player1_id, ws1 = queue.pop(0)
            has_two_different_players = False
            for i, (player2_id, ws2) in enumerate(queue):
                if player1_id != player2_id:
                    has_two_different_players = True
                    queue.pop(i)

                    game_id = str(uuid4())

                    active_lobbies[game_id] = (player1_id, player2_id)

                    token1 = jwt.encode(
                        {"game_id": game_id, "players": [player1_id, player2_id]},
                        SECRET_KEY,
                        algorithm="HS256",
                    )
                    token2 = jwt.encode(
                        {"game_id": game_id, "players": [player1_id, player2_id]},
                        SECRET_KEY,
                        algorithm="HS256",
                    )

                    await ws1.send_json({"token": token1})
                    await ws2.send_json({"token": token2})

                    await ws1.close()
                    await ws2.close()

            if not has_two_different_players:
                queue.append((player1_id, ws1))
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(1)


@app.websocket("/ws/join-lobby/{player_id}/{player_secret}")
async def join_lobby(websocket: WebSocket, player_id: str, player_secret: str):
    """
    Adiciona um jogador à fila de lobby.
    """
    md5_hash = f'{player_id}:{player_secret}'.encode('utf-8')
    md5_hash = hashlib.md5(md5_hash).hexdigest()
    try:
        if not Broker.get(f'player_id_secret:{md5_hash}'):
            logging.warning("Player not found")
            raise HTTPException(status_code=401, detail="Forbidden")
    except Exception as e:
        logging.warning("Exception if not Broker.get(f'player_id_secret:{md5_hash}'):")
        logging.warning(e)
        raise HTTPException(status_code=401, detail="Forbidden")

    await websocket.accept()
    global queue
    queue.append((player_id, websocket))
    try:
        await websocket.send_json({"message": "waiting_for_match"})
        while True:
            await asyncio.sleep(1)  # Mantém a conexão aberta
    except WebSocketDisconnect:
        # Remove o jogador da fila caso desconecte
        queue = [item for item in queue if item[1] != websocket]


# Roda a função de emparelhamento de forma contínua
@app.on_event("startup")
async def start_matchmaking():
    asyncio.create_task(create_match())
