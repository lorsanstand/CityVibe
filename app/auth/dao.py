from auth.models import RefreshSessionModel
from auth.schemas import RefreshSessionUpdate, RefreshSessionCreate
from base_dao import BaseDAO


class RefreshSessionDAO(BaseDAO[RefreshSessionModel, RefreshSessionCreate, RefreshSessionUpdate]):
    model = RefreshSessionModel