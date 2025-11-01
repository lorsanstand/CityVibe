from app.auth.models import RefreshSessionModel
from app.auth.schemas import RefreshSessionUpdate, RefreshSessionCreate
from app.base_dao import BaseDAO


class RefreshSessionDAO(BaseDAO[RefreshSessionModel, RefreshSessionCreate, RefreshSessionUpdate]):
    model = RefreshSessionModel