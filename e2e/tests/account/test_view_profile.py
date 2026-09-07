import re

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.test_utils import build_image_bytes
from e2e.pages.account_detail_page import AccountDetailPage
from e2e.pages.login_page import LoginPage


@pytest.mark.e2e
class TestViewProfile:
    def test_user_can_view_own_profile(self, logged_in_profile_detail_page, profile_user):
        logged_in_profile_detail_page.expect_name(profile_user.name)
        logged_in_profile_detail_page.expect_email(profile_user.email)
        logged_in_profile_detail_page.expect_actions_present()
        logged_in_profile_detail_page.expect_security_section_visible()

    def test_user_can_view_profile_of_roommate(
        self, page, base_url, profile_user, roommate, shared_room, user_password
    ):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, user_password)

        roommate_path = reverse("account:detail", kwargs={"pk": roommate.id})
        detail_page = AccountDetailPage(page, base_url, roommate_path)
        detail_page.navigate()

        detail_page.expect_member_name(roommate.name)
        detail_page.expect_actions_absent()
        detail_page.expect_security_section_hidden()

    def test_user_can_look_at_the_photo_of_a_roommate_full_size(
        self, page, base_url, profile_user, roommate, shared_room, user_password
    ):
        roommate.profile_picture.save("avatar.png", ContentFile(build_image_bytes()), save=True)

        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, user_password)

        roommate_path = reverse("account:detail", kwargs={"pk": roommate.id})
        detail_page = AccountDetailPage(page, base_url, roommate_path)
        detail_page.navigate()

        detail_page.open_photo_preview_dialog()
        detail_page.expect_photo_preview_shows(roommate.profile_picture_url)
        detail_page.close_photo_preview_dialog()

    def test_a_roommate_without_a_photo_offers_no_preview(
        self, page, base_url, profile_user, roommate, shared_room, user_password
    ):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, user_password)

        roommate_path = reverse("account:detail", kwargs={"pk": roommate.id})
        detail_page = AccountDetailPage(page, base_url, roommate_path)
        detail_page.navigate()

        detail_page.expect_no_photo_preview()

    def test_user_cannot_view_profile_of_unrelated_user(
        self, page, base_url, profile_user, unrelated_user, user_password
    ):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, user_password)

        unrelated_path = reverse("account:detail", kwargs={"pk": unrelated_user.id})
        response = page.goto(f"{base_url}{unrelated_path}")

        expected_status_code_forbidden = 403
        assert response.status == expected_status_code_forbidden

    def test_superuser_can_view_any_profile(self, page, base_url, superuser, unrelated_user, user_password):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(superuser.email, user_password)

        path = reverse("account:detail", kwargs={"pk": unrelated_user.id})
        detail_page = AccountDetailPage(page, base_url, path)
        detail_page.navigate()

        detail_page.expect_member_name(unrelated_user.name)

    def test_guest_sees_guest_mode_banner_on_own_profile(self, logged_in_guest_detail_page):
        logged_in_guest_detail_page.expect_guest_mode_banner_visible()

    def test_anonymous_visitor_is_redirected_to_login(self, page, base_url, profile_user):
        path = reverse("account:detail", kwargs={"pk": profile_user.id})
        page.goto(f"{base_url}{path}")

        expect(page).to_have_url(re.compile(re.escape(reverse("account:login"))))
