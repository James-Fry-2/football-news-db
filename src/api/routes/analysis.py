from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.db.models.article import Article as ArticleModel
from src.db.models.player import Player as PlayerModel
from src.db.models.team import Team as TeamModel
from src.db.database import Database
from pydantic import BaseModel

router = APIRouter()

class AnalysisResponse(BaseModel):
    total_articles: int
    articles_by_source: Dict[str, int]
    articles_by_team: Dict[str, int]
    articles_by_player: Dict[str, int]

async def get_db():
    async for session in Database.get_session():
        yield session

@router.get("/stats", response_model=AnalysisResponse)
async def get_analysis_stats(
    db: AsyncSession = Depends(get_db)
):
    # Get total articles
    total_query = select(func.count(ArticleModel.id))
    total_result = await db.execute(total_query)
    total_articles = total_result.scalar_one()

    # Get articles by source
    source_query = select(
        ArticleModel.source,
        func.count(ArticleModel.id).label('count')
    ).group_by(ArticleModel.source)
    source_result = await db.execute(source_query)
    articles_by_source = {row.source: row.count for row in source_result}

    # Get articles by team
    team_query = select(
        TeamModel.name,
        func.count(ArticleModel.id).label('count')
    ).join(ArticleModel.teams).group_by(TeamModel.name)
    team_result = await db.execute(team_query)
    articles_by_team = {row.name: row.count for row in team_result}

    # Get articles by player
    player_query = select(
        PlayerModel.name,
        func.count(ArticleModel.id).label('count')
    ).join(ArticleModel.players).group_by(PlayerModel.name)
    player_result = await db.execute(player_query)
    articles_by_player = {row.name: row.count for row in player_result}

    return AnalysisResponse(
        total_articles=total_articles,
        articles_by_source=articles_by_source,
        articles_by_team=articles_by_team,
        articles_by_player=articles_by_player
    ) 