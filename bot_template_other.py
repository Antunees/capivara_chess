import asyncio
import json
import websockets
import logging
import time
import random

import requests
import jwt


player_id = '7b8f0445-8128-4e82-ae6b-5a2e9a646ae9'
player_secret = '5e9a1ba8-8fb2-4f11-a2d0-01cc65df749c'
game_id = ''

def start_game(pool_host, pool_port, game_token):
    url = f"http://{pool_host}:{pool_port}/start_game?token={game_token}"

    response = requests.request("POST", url, headers={}, data={})

    return response.json()

async def request_game(player_id, player_secret):
    """
    Conecta um jogador ao WebSocket e processa as mensagens recebidas.
    """
    try:
        mode = 'casual'
        url = f"ws://10.20.1.204:9002/ws/join-lobby/{player_id}/{player_secret}/{mode}"
        async with websockets.connect(url) as websocket:
            logging.warning(f"Jogador {player_id} conectado ao lobby.")

            try:
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    if "token" in data:
                        logging.warning(f"Jogador {player_id} recebeu token JWT: {data['token']}")
                        return data['token']
                    else:
                        logging.warning(f"Jogador {player_id} recebeu: {data}")
            except websockets.ConnectionClosed:
                logging.warning(f"Jogador {player_id} foi desconectado.")
            except Exception as e:
                logging.warning(f"Erro no jogador {player_id}: {e}")
    except Exception as e:
        logging.warning(f"Erro no jogador {player_id}: {e}")

def get_status(pool_host, pool_port, game_id):
    url = f"http://{pool_host}:{pool_port}/check_status/{game_id}"

    response = requests.request("GET", url, headers={}, data={})

    if response.status_code != 200:
        logging.warning('game end')
        logging.warning(response.json())
        exit(1)

    return response.json()

def get_legal_moves(pool_host, pool_port, game_id):
    url = f"http://{pool_host}:{pool_port}/get_legal_moves/{game_id}"

    response = requests.request("GET", url, headers={}, data={})

    if response.status_code != 200:
        logging.warning('get_legal_moves')
        logging.warning(response.json())
        exit(1)

    return response.json()

def make_move(pool_host, pool_port, game_id, move: str):
    url = f"http://{pool_host}:{pool_port}/make_move/{game_id}?player_id={player_id}"

    data = {
        'move': move
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(data))

    if response.status_code not in [200, 401, 403]:
        logging.warning(f'make_move - {move} - {response.status_code}')
        logging.warning(response.json())
        exit(1)

    return response.status_code == 200

async def main():
    game_token = await request_game(player_id, player_secret)

    token1 = jwt.decode(
        game_token,
        options={"verify_signature": False}
    )
    game_id = token1['game_id']
    pool_host = token1['pool_address']['host']
    pool_port = token1['pool_address']['port']

    match_info = start_game(pool_host, pool_port, game_token)
    player_color = 'white' if match_info['white'] == player_id else 'black'


    running = True

    while running:
        status = get_status(pool_host, pool_port, game_id)
        running = status['status'] == 'ongoing'

        if status['turn'] != player_color:
            logging.warning("waiting turn")
            time.sleep(1)
            continue

        legal_moves = get_legal_moves(pool_host, pool_port, game_id)['legal_moves']

        random.shuffle(legal_moves)
        if make_move(pool_host, pool_port, game_id, legal_moves[0]):
            logging.warning('move maded')


        time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())