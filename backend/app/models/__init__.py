"""SQLAlchemy models.

Models are imported here so that ``Base.metadata`` always contains every table
when the application or test suite starts.
"""

from app.models.auction import Auction, AuctionBid
from app.models.game import Game, GameEvent, GameStatus, PlayerState
from app.models.user import Role, User

__all__ = [
    "Auction",
    "AuctionBid",
    "Game",
    "GameEvent",
    "GameStatus",
    "PlayerState",
    "Role",
    "User",
]
