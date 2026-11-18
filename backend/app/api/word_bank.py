from fastapi import APIRouter

from app.schemas.word import WordDto
from app.util.word_bank import default_words

router = APIRouter(prefix="/word-bank", tags=["word-bank"])


@router.get("/default", response_model=list[WordDto])
async def get_default_words() -> list[WordDto]:
    return [WordDto(word=word, base_score=len(word) ** 2) for word in default_words()]
