import asyncio
from uuid import uuid4
import websockets
import json

async def connect_player(player_id):
    """
    Conecta um jogador ao WebSocket e processa as mensagens recebidas.
    """
    url = f"ws://localhost:9002/ws/join-lobby/{player_id}"
    async with websockets.connect(url) as websocket:
        print(f"Jogador {player_id} conectado ao lobby.")

        try:
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if "token" in data:
                    print(f"Jogador {player_id} recebeu token JWT: {data['token']}")
                else:
                    print(f"Jogador {player_id} recebeu: {data}")
        except websockets.ConnectionClosed:
            print(f"Jogador {player_id} foi desconectado.")
        except Exception as e:
            print(f"Erro no jogador {player_id}: {e}")

async def main():
    """
    Simula múltiplos jogadores entrando na fila de lobby.
    """
    players = [uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4()]  # IDs dos jogadores
    tasks = [connect_player(player_id) for player_id in players]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
