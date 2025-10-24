from base_dao import BaseDAO

from users.models import UserModel
from users.schemas import UserCreateDB, UserUpdateDB


class UserDao(BaseDAO[UserModel, UserCreateDB, UserUpdateDB]):
    model = UserModel