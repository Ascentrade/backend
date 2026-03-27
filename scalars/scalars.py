import strawberry
from typing import NewType, Optional
import datetime
from decimal import Decimal

# 64-bit safe integer scalar; serialized as string in GraphQL/JSON to avoid precision loss
BigInt = NewType("BigInt", int)

# Historical Data types
@strawberry.type
class HistoricalDataPoint:
    id: strawberry.ID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    date: datetime.date
    open: Optional[Decimal]
    high: Optional[Decimal]
    low: Optional[Decimal]
    close: Optional[Decimal]
    volume: Optional[Decimal]
    bar_count: Optional[int]
    ema_20: Optional[Decimal]
    sma_50: Optional[Decimal]
    sma_200: Optional[Decimal]
    rsi: Optional[Decimal]
    bb_pc: Optional[Decimal]
    adx: Optional[Decimal]
    dmip: Optional[Decimal]
    dmim: Optional[Decimal]

@strawberry.type
class AiResponse:
    id: strawberry.ID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    timestamp: datetime.datetime
    response: str
    confidence: int
    score: int
    # KEEP: Uncomment when data is needed in frontend
    #prompt: str
    #data: dict

@strawberry.type
class AiResponseSeriesPoint:
    date: datetime.date
    confidence: int
    score: int
