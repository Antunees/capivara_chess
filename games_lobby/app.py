import json
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Tuple
from uuid import uuid4
import jwt
import asyncio
import hashlib
import time

from broker_db import Broker

SECRET_KEY = os.getenv("SECRET_KEY")
app = FastAPI()

global queue
queue: List[Tuple[str, WebSocket, str, float]] = []

active_lobbies: Dict[str, Tuple[str, str]] = {}


async def create_match():
    """
    Create a match for two differents players on queue
    """
    while True:
        on_queue = len(queue)
        logging.warning(f'{on_queue} on Queue')
        if len(queue) >= 2:
            player1_id, ws1, mode, timestamp_register = queue.pop(0)
            has_founded_match = False

            for i, (player2_id, ws2, mode2, timestamp_register2) in enumerate(queue):
                if player1_id != player2_id and mode == mode2:
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

                    try:
                        await ws1.send_json({"token": token1})
                    except Exception as e:
                        logging.warning('start_matchmaking ws1.send_json Error')
                        logging.warning(str(e))
                        queue.append((player2_id, ws2, mode2, timestamp_register2))
                        continue
                    try:
                        await ws2.send_json({"token": token2})
                    except Exception as e:
                        logging.warning('start_matchmaking ws2.send_json Error')
                        logging.warning(str(e))
                        queue.append((player2_id, ws2, mode2, timestamp_register2))
                        continue

                    try:
                        await ws1.close()
                    except Exception as e:
                        logging.warning('start_matchmaking ws1.close Error')
                        logging.warning(str(e))
                        queue.append((player2_id, ws2, mode2, timestamp_register2))
                        continue
                    try:
                        await ws2.close()
                    except Exception as e:
                        logging.warning('start_matchmaking ws2.close Error')
                        logging.warning(str(e))
                        queue.append((player2_id, ws2, mode2, timestamp_register2))
                        continue

                    has_founded_match = True

            if not has_founded_match:
                timestamp_atual = time.time()
                # If more than 30 seconds on queue, remove
                if timestamp_atual - timestamp_register <= 60:
                    queue.append((player1_id, ws1, mode, timestamp_register))
                else:
                    try:
                        await ws1.send_json({"message": 'Expired time on queue'})
                        await ws1.close()
                    except Exception as e:
                        logging.warning('start_matchmaking Expired time on queue Error')
                        logging.warning(str(e))
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

    timestamp_register = time.time()

    await websocket.accept()
    global queue
    queue.append((player_id, websocket, mode, timestamp_register))
    try:
        await websocket.send_json({"message": "waiting_for_match"})
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        queue = [item for item in queue if item[1] != websocket]


@app.on_event("startup")
async def start_matchmaking():
    try:
        asyncio.create_task(create_match())
    except Exception as e:
        logging.warning('start_matchmaking Error')
        logging.warning(str(e))
        exit(1)
