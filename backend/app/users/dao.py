from app.base_dao import BaseDAO

from app.users.models import UserModel, UserEventFavoritesModel
from app.users.schemas import UserCreateDB, UserUpdateDB, UserEventFavoritesCreateDB, UserEventFavoritesUpdateDB


class UserDao(BaseDAO[UserModel, UserCreateDB, UserUpdateDB]):
    model = UserModel


class UserEventFavoritesDao(BaseDAO[UserEventFavoritesModel, UserEventFavoritesCreateDB, UserEventFavoritesUpdateDB]):
    model = UserEventFavoritesModel