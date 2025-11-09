from app.base_dao import BaseDAO

from app.events.models import EventModel
from app.events.schemas import EventCreateDB, EventUpdateDB


class EventDao(BaseDAO[EventModel, EventCreateDB, EventUpdateDB]):
    model = EventModel