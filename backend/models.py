from pydantic import BaseModel
from typing import Optional, Literal

GrainKey = Literal["aquatique", "poussiéreux", "texture", "minéral", "saturé", "épuré"]
SensationKey = Literal["hypnotique", "mystérieux", "rituel", "organique", "acide", "amorphe", "cinématique", "nerveux"]
MasseBassKey = Literal["lourd", "squelette", "léger"]
RoleSetKey = Literal["amorce", "construction", "peak_time", "planage"]


class TrackBase(BaseModel):
    name: str
    artist: str
    album: Optional[str] = None
    label: Optional[str] = None
    year: Optional[int] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    grain: Optional[GrainKey] = None
    sensations: list[SensationKey] = []
    masse_basse: Optional[MasseBassKey] = None
    role_set: Optional[RoleSetKey] = None
    url: Optional[str] = None
    downloaded: bool = False
    hq_download: bool = False
    notes: Optional[str] = None
    layering: Optional[str] = None


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    name: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    label: Optional[str] = None
    year: Optional[int] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    grain: Optional[GrainKey] = None
    sensations: Optional[list[SensationKey]] = None
    masse_basse: Optional[MasseBassKey] = None
    role_set: Optional[RoleSetKey] = None
    url: Optional[str] = None
    downloaded: Optional[bool] = None
    hq_download: Optional[bool] = None
    notes: Optional[str] = None
    layering: Optional[str] = None


class Track(TrackBase):
    id: int
    notion_id: Optional[str] = None

    class Config:
        from_attributes = True


class SpotifyLookupRequest(BaseModel):
    url: str


class SpotifyTrackMeta(BaseModel):
    name: str
    artist: str
    label: Optional[str] = None
    year: Optional[int] = None
    url: str
    image_url: Optional[str] = None
