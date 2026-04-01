"""
 @copyright Copyright (C) 2026 Dennis Einloft <dev@greguhn.de>
 
 @author Dennis Einloft <dev@greguhn.de>
 
 @license AGPL-3.0-or-later
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.
 
 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import typing
import datetime

import strawberry
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    HistoricalDataModel,
    AiResponseModel
)
from scalars.scalars import (
    AiResponseSeriesPoint,
    HistoricalDataPoint,
    AiResponse
)

from logging_config import get_logger
logger = get_logger(__name__)


@strawberry.type
class Query:

	@strawberry.field
	async def get_historical_data(self, info: strawberry.Info, limit: typing.Optional[int] = None) -> typing.List[HistoricalDataPoint]:
		session: AsyncSession = info.context["session"]
		two_years_ago = datetime.date.today() - datetime.timedelta(days=365 * 2)
		query = (
			select(HistoricalDataModel)
			.where(HistoricalDataModel.date >= two_years_ago)
			.order_by(HistoricalDataModel.date.desc())
		)
		if limit:
			query = query.limit(limit)
		result = await session.execute(query)
		return result.scalars().all()

	@strawberry.field
	async def get_ai_response(self, info: strawberry.Info, date: datetime.date) -> typing.Optional[AiResponse]:
		session: AsyncSession = info.context["session"]
		query = (
			select(AiResponseModel)
			.where(func.date(AiResponseModel.timestamp) == date)
			.order_by(AiResponseModel.timestamp.desc())
			.limit(1)
		)
		result = await session.execute(query)
		return result.scalars().first()
	
	@strawberry.field
	async def get_ai_responses_series(self, info: strawberry.Info) -> typing.List[AiResponseSeriesPoint]:
		session: AsyncSession = info.context["session"]
		timestamp_date = func.date(AiResponseModel.timestamp).label("date")
		latest_per_day = (
			select(
				timestamp_date,
				func.max(AiResponseModel.timestamp).label("latest_timestamp")
			)
			.group_by(timestamp_date)
			.subquery()
		)

		query = (
			select(
				latest_per_day.c.date,
				AiResponseModel.confidence,
				AiResponseModel.score
			)
			.join(
				AiResponseModel,
				(AiResponseModel.timestamp == latest_per_day.c.latest_timestamp)
				& (func.date(AiResponseModel.timestamp) == latest_per_day.c.date)
			)
			.order_by(latest_per_day.c.date.asc())
		)
		result = await session.execute(query)
		rows = result.all()
		return [
			AiResponseSeriesPoint(date=row.date, confidence=row.confidence, score=row.score)
			for row in rows
		]
