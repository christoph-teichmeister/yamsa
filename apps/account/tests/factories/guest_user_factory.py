from apps.account.tests.factories.user_factory import UserFactory


class GuestUserFactory(UserFactory):
    is_guest = True
