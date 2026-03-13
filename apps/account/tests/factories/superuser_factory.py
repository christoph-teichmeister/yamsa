from .user_factory import UserFactory


class SuperuserFactory(UserFactory):
    is_staff = True
    is_superuser = True
