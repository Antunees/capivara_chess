from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

# Configuração do banco de dados
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@games_database/{POSTGRES_DB}"
# DATABASE_URL = f"postgresql://user:password@localhost/chess_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos de banco de dados
class Player(Base):
    __tablename__ = "players"
    player_id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_email = Column(String, unique=True, index=True)
    rating = Column(Integer, default=1200)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Game(Base):
    __tablename__ = "games"
    game_id = Column(Integer, primary_key=True, index=True)
    player_white = Column(Integer, ForeignKey('players.player_id'))
    player_black = Column(Integer, ForeignKey('players.player_id'))
    start_time = Column(TIMESTAMP, default=datetime.utcnow)
    end_time = Column(TIMESTAMP)
    result = Column(String(20))  # 'white_win', 'black_win', 'draw'
    winner = Column(Integer, ForeignKey('players.player_id'), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    player1 = relationship("Player", foreign_keys=[player_white])
    player2 = relationship("Player", foreign_keys=[player_black])

# Criação do banco de dados
Base.metadata.create_all(bind=engine)

# Instanciação do FastAPI
app = FastAPI()

# Função para obter sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para criar um jogador
@app.post("/players/")
def create_player(player_name: str, player_email: str, db: Session = Depends(get_db)):
    db_player = Player(player_name=player_name, player_email=player_email)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

# Endpoint para registrar uma partida
@app.post("/games/")
def create_game(player_white: int, player_black: int, db: Session = Depends(get_db)):
    db_game = Game(player_white=player_white, player_black=player_black)
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

# Endpoint para registrar o resultado de uma partida
@app.post("/games/{game_id}/result/")
def register_result(game_id: int, result: str, db: Session = Depends(get_db)):
    db_game = db.query(Game).filter(Game.game_id == game_id).first()
    if db_game is None:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    db_game.result = result
    if result == "white_win":
        db_game.winner = db_game.player_white
    elif result == "black_win":
        db_game.winner = db_game.player_black
    else:
        db_game.winner = None

    db_game.end_time = datetime.utcnow()
    db.commit()
    db.refresh(db_game)
    return db_game

# Endpoint para gerar ranking
@app.get("/ranking/")
def get_ranking(db: Session = Depends(get_db)):
    players = db.query(Player).order_by(Player.rating.desc()).all()
    ranking = [{"rank": idx+1, "player_name": player.player_name, "rating": player.rating} for idx, player in enumerate(players)]
    return {"ranking": ranking}
