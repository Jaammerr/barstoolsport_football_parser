from pydantic import BaseModel


class FootballMatchSpread(BaseModel):
    spread: str
    moneyline: str


class FootballTotalPoints(BaseModel):
    total: str
    moneyline: str


class FootballTeamData(BaseModel):
    name: str
    score: str
    spread: str
    total: str
    moneyline: str
    match_spreads: list[FootballMatchSpread] = []
    total_points: list[FootballTotalPoints] = []


class FootballEventData(BaseModel):
    id: str
    startDate: str
    teams: list[FootballTeamData]


class FootballLeagueEventsList(BaseModel):
    leagueName: str
    events: list[FootballEventData]
