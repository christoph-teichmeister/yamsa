from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.importer.services.person_candidate_service import PersonCandidateService
from apps.room.models import Room


class TestPersonCandidateService:
    def test_guests_from_other_rooms_are_offered(self, db: None, user: User, room: Room, guest_user: User):
        candidates = PersonCandidateService(user=user).get_candidates()

        assert guest_user in candidates

    def test_the_importer_is_not_a_candidate(self, db: None, user: User, room: Room):
        assert user not in PersonCandidateService(user=user).get_candidates()

    def test_name_match_ignores_case_and_padding(self, db: None, user: User, room: Room):
        friend = UserFactory(name="Elisabeth")
        room.users.add(friend)
        service = PersonCandidateService(user=user)

        assert service.match_by_name("  elisabeth ", service.get_candidates()) == friend

    def test_unknown_name_matches_nothing(self, db: None, user: User, room: Room):
        assert PersonCandidateService(user=user).match_by_name("Nobody", []) is None
