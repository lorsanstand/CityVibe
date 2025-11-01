from app.base_dao import BaseDAO

from app.users.models import UserModel
from app.users.schemas import UserCreateDB, UserUpdateDB


class UserDao(BaseDAO[UserModel, UserCreateDB, UserUpdateDB]):
    model = UserModel