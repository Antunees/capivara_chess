# Capivara Chess

O objetivo deste jogo é criar um desafio de lógica, onde o desenvolvedor vai criar um `bot` para jogar as partidas. Como o objetivo é lógica, então não é permitido o uso de funções prontas de Xadrez, o desenvolvedor deve criar suas funções e lógica para decidir quais são os melhores movimentos e então vencer a partida.

Toda comunicação é feita através de API, sendo elas websocket e REST, então o bot pode ser escrito na liguagem de preferencia do desenvolvedor.

Que vença a melhor lógica!

![Wallpaper](wallpaper.jpeg)
## Endpoints

1. Criar usuário
    Por enquanto deve ser solicitado a um ADM
    Ele irá criar o usuário e irá informar os dados de acesso:
    * ID de usuário
    * Secret
2. Entrar na fila de partidas
   Este endpoint é para uma conexão de websocket, o endereço é:
   ws://{Endereço do servidor}/ws/join-lobby/{id de usuário}/{Secret}/{Modo de jogo}

   Exemplo

   ``` python
    url = f"ws://10.20.1.204:9002/ws/join-lobby/eqdq21d21/d1232d1d1/casual"
   ```

    * Modo de jogo: Por enquanto esse parametro apenas separa as filas. Então o valor padrão deve ser "casual", mas também pode ser usado para caso queira jogar com alguém especifico, nesse caso deve combinar um valor com a pessoa e os dois utilizarem o mesmo, exemplo: capivaraxjacare.

    * Obs.: A fila tem um tempo limite de permanencia, então ao final irá retornar uma mensagem e remover o usuário da fila. Você deve entrar novamente na fila

3. Recebendo uma partida
   O corpo da resposta de solitar uma partida será um json com o indice `token`, o valor do token será um jwt, esse jwt é o GAME_TOKEN.

   Dentro do jwt possui os seguintes indices: game_id, players (contém uma lista com o ID dos usuários da partida), pool_address (contém o endereço da partida)

    Exemplo de jwt (GAME_TOKEN): `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJnYW1lX2lkIjoiYWRjNmI2ZDgtZjllOS00YTA3LWJhMDEtYTJlYmJiMGQ2YjkyIiwicGxheWVycyI6WyI0Yzg4YjZhNC00NGRmLTRkMjctOWFkZC0zNWMzYWMwZWRlODYiLCI3YjhmMDQ0NS04MTI4LTRlODItYWU2Yi01YTJlOWE2NDZhZTkiXSwicG9vbF9hZGRyZXNzIjp7Imhvc3QiOiIxMC4yMC4xLjIwNCIsInBvcnQiOiI5MDAwIn19.JMNjqc8mgQ1fmNXyhAE7kgDM4UB-pdxkMElEzi4nMuE`

    ``` json
    {
        "game_id": "adc6b6d8-f9e9-4a07-ba01-a2ebbb0d6b92",
        "players": [
            "4c88b6a4-44df-4d27-9add-35c3ac0ede86",
            "7b8f0445-8128-4e82-ae6b-5a2e9a646ae9"
        ],
        "pool_address": {
            "host": "192.168.1.1",
            "port": "9000"
        }
    }
    ```

4. Iniciando a partida
   Tendo então o ID da partida e o endereço, deve iniciar a partida chamando o endpoint abaixo:
   http://{POOL_HOST}:{POOL_PORT}/start_game?token={GAME_TOKEN}

   A resposta da requisição é um json informando a cor de cada usuário, sendo as chaves: `white` e `black`
5. Neste ponto você terá uma partida já iniciada, então não precisa mais seguir uma ordem e utilizar todos os endpoints. Daqui em diante vai de acordo com a estrategia de cada um.
Irei citar apenas 3 principais endpoints na minha opnião, mas acessando as docs da API, poderá ver os outros endpoints

* Verificando o status, para saber se a partida terminou, e se sim, quem venceu, para saber também de quem é a vez e o tempo restante.
* Obter os movimentos disponíveis no momento
* Fazer movimento, seguindo a regra dos movimentos disponíveis
