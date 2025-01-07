import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Tuple
from uuid import uuid4
import jwt
import asyncio

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
            # Pega os dois primeiros jogadores da fila
            player1_id, ws1 = queue.pop(0)
            player2_id, ws2 = queue.pop(0)
            game_id = str(uuid4())

            # Armazena o lobby criado
            active_lobbies[game_id] = (player1_id, player2_id)

            # Cria tokens JWT para ambos os jogadores
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

            # Envia o token para ambos os jogadores
            await ws1.send_json({"token": token1})
            await ws2.send_json({"token": token2})

            # Fecha as conexões WebSocket
            await ws1.close()
            await ws2.close()
        else:
            await asyncio.sleep(1)  # Aguarda antes de verificar novamente


@app.websocket("/ws/join-lobby/{player_id}")
async def join_lobby(websocket: WebSocket, player_id: str):
    """
    Adiciona um jogador à fila de lobby.
    """
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
