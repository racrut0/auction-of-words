from app.schemas.common import CamelModel


class WordDto(CamelModel):
    word: str
    base_score: int
