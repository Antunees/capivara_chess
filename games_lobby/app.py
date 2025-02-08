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

global queue
queue: List[Tuple[str, WebSocket, str]] = []

active_lobbies: Dict[str, Tuple[str, str]] = {}


async def create_match():
    """
    Create a match for two differents players on queue
    """
    while True:
        if len(queue) >= 2:
            player1_id, ws1, mode = queue.pop(0)
            has_founded_match = False
            for i, (player2_id, ws2, mode2) in enumerate(queue):
                if player1_id != player2_id and mode == mode2:
                    has_founded_match = True
                    queue.pop(i)

                    game_id = str(uuid4())

                    active_lobbies[game_id] = (player1_id, player2_id)

                    pool_address = {
                        'host': '10.20.1.204',
                        'port': '9000'
                    }
                    token1 = jwt.encode(
                        {"game_id": game_id, "players": [player1_id, player2_id], "pool_address": pool_address},
                        SECRET_KEY,
                        algorithm="HS256",
                    )
                    token2 = jwt.encode(
                        {"game_id": game_id, "players": [player1_id, player2_id], "pool_address": pool_address},
                        SECRET_KEY,
                        algorithm="HS256",
                    )

                    await ws1.send_json({"token": token1})
                    await ws2.send_json({"token": token2})

                    await ws1.close()
                    await ws2.close()

            if not has_founded_match:
                queue.append((player1_id, ws1, mode))
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(1)


@app.websocket("/ws/join-lobby/{player_id}/{player_secret}/{mode}")
async def join_lobby(websocket: WebSocket, player_id: str, player_secret: str, mode: str):
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
    queue.append((player_id, websocket, mode))
    try:
        await websocket.send_json({"message": "waiting_for_match"})
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        queue = [item for item in queue if item[1] != websocket]


@app.on_event("startup")
async def start_matchmaking():
    asyncio.create_task(create_match())
