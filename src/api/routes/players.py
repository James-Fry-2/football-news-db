from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.player import Player as PlayerModel
from src.db.database import Database
from pydantic import BaseModel

router = APIRouter()

class PlayerBase(BaseModel):
    name: str

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(PlayerBase):
    name: Optional[str] = None

class Player(PlayerBase):
    id: int

    class Config:
        from_attributes = True

async def get_db():
    async for session in Database.get_session():
        yield session

@router.get("/", response_model=List[Player])
async def get_players(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(PlayerModel).offset(skip).limit(limit)
    result = await db.execute(query)
    players = result.scalars().all()
    return players

@router.get("/{player_id}", response_model=Player)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(PlayerModel).where(PlayerModel.id == player_id)
    result = await db.execute(query)
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.post("/", response_model=Player)
async def create_player(
    player: PlayerCreate,
    db: AsyncSession = Depends(get_db)
):
    db_player = PlayerModel(**player.model_dump())
    db.add(db_player)
    await db.commit()
    await db.refresh(db_player)
    return db_player

@router.put("/{player_id}", response_model=Player)
async def update_player(
    player_id: int,
    player: PlayerUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(PlayerModel).where(PlayerModel.id == player_id)
    result = await db.execute(query)
    db_player = result.scalar_one_or_none()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    update_data = player.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_player, key, value)
    
    await db.commit()
    await db.refresh(db_player)
    return db_player 