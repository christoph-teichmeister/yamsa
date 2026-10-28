from playwright.sync_api import APIResponse, Page


class BasePage:
    def __init__(self, page: Page, base_url: str, path: str | None = None) -> None:
        self.page = page
        self.base_url = base_url
        self.path = path

    def navigate(self) -> None:
        self.page.goto(f"{self.base_url}{self.path}")
        self.page.wait_for_load_state("load")

    def post(self, path: str, data: dict[str, str] | None = None) -> APIResponse:
        """POST as the logged-in browser session, the way a form would, but without a UI to click.

        For requests the interface offers no button for (un-settling a debt) or deliberately
        hides (editing in a closed room).
        """
        csrf_token = next(
            cookie["value"] for cookie in self.page.context.cookies(self.base_url) if cookie["name"] == "csrftoken"
        )
        return self.page.request.post(
            f"{self.base_url}{path}",
            form=data or {},
            headers={"X-CSRFToken": csrf_token, "Referer": f"{self.base_url}{path}"},
            max_redirects=0,
        )
