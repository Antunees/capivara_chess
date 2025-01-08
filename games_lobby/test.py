import asyncio
from uuid import uuid4
import websockets
import json

async def connect_player(player_id, player_secret):
    """
    Conecta um jogador ao WebSocket e processa as mensagens recebidas.
    """
    try:
        url = f"ws://localhost:9002/ws/join-lobby/{player_id}/{player_secret}"
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
    except Exception as e:
        print(f"Erro no jogador {player_id}: {e}")

async def main():
    """
    Simula múltiplos jogadores entrando na fila de lobby.
    """
    players = [uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4()]  # IDs dos jogadores
    # tasks = [connect_player(player_id, "a") for player_id in players]
    tasks = [
        # connect_player('54f24c69-8ca6-4c4e-9edb-9abb946ad902', 'abf39507-2d02-4234-be04-6d053415045f'), # cap
        # connect_player('54f24c69-8ca6-4c4d-9edb-9abb946ad902', 'abf39507-2d02-4234-be04-6d053415045f'), # cap WRONG
        connect_player('775e3aae-c22a-44bd-b439-5819a477dd09', 'f67c6aee-80d5-4c83-b1ee-732c405618ee'), # cap2
        connect_player('775e3aae-c22a-44bd-b439-5819a477dd09', 'f67c6aee-80d5-4c83-b1ee-732c405618ee'), # cap2
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
