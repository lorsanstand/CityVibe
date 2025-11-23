from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.base_dao import BaseDAO

from app.events.models import EventModel
from app.events.schemas import EventCreateDB, EventUpdateDB

from app.events.models import EventReviewsModel
from app.events.schemas import EventReviewsCreateDB, EventReviewsUpdateDB


class EventDao(BaseDAO[EventModel, EventCreateDB, EventUpdateDB]):
    model = EventModel


class EventReviewsDao(BaseDAO[EventReviewsModel, EventReviewsCreateDB, EventReviewsUpdateDB]):
    model = EventReviewsModel

    @classmethod
    async def avg_rating(
            cls,
            session: AsyncSession,
            *filter,
            **filter_by
    ):
        stmt = select(func.avg(EventReviewsModel.rating)).filter(*filter).filter_by(**filter_by)
        avg_rating = await session.execute(stmt)
        return avg_rating.scalar()