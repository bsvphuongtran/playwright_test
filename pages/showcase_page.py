from playwright.sync_api import FrameLocator, Page, expect

from pages.base_page import BasePage


class ShowcasePage(BasePage):
  def __init__(self, page: Page, base_url: str) -> None:
    super().__init__(page)
    self.base_url = base_url

  def open(self) -> None:
    self.page.goto(self.base_url)

  def demo_frame(self) -> FrameLocator:
    return self.page.frame_locator("#demo-iframe")

  def frame_alpha(self) -> FrameLocator:
    return self.page.frame_locator("#iframe-A")

  def frame_beta(self) -> FrameLocator:
    return self.frame_alpha().frame_locator("#iframe-B")

  def frame_gamma(self) -> FrameLocator:
    return self.frame_beta().frame_locator("#iframe-C")

  def load_nested_frames(self) -> None:
    self.page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    expect(self.frame_alpha().get_by_text("Iframe A")).to_be_visible()

  def open_iframe_beta(self) -> None:
    self.frame_alpha().get_by_role("button", name="Open Iframe B").click()
    expect(self.frame_beta().get_by_text("Iframe B")).to_be_visible()

  def open_iframe_gamma(self) -> None:
    self.frame_beta().get_by_role("button", name="Open Iframe C").click()
    expect(self.frame_gamma().get_by_text("Iframe C")).to_be_visible()

  def open_modal(self) -> None:
    self.page.get_by_role("button", name="Open In-page Modal").click()
    expect(self.page.locator("#modal-overlay.active")).to_be_visible()

  def expect_modal_closed(self) -> None:
    expect(self.page.locator("#modal-overlay.active")).not_to_be_visible()

  def click_normal_state(self) -> None:
    self.page.locator("#btn-reset-state").click()

  def click_failure_state(self) -> None:
    self.page.locator("#btn-trigger-failure").click()

  def expect_vr_full_normal(self) -> None:
    expect(self.page.locator("#vr-full-display")).to_contain_text("System Normal")

  def expect_vr_full_failure(self) -> None:
    expect(self.page.locator("#vr-full-display")).to_contain_text("CRITICAL FAILURE EMULATED")

  def play_sequence(self) -> None:
    self.page.locator("#btn-play-seq").click()

  def expect_sequence_complete(self, timeout: int = 10_000) -> None:
    expect(self.page.locator("#vr-action-txt")).to_have_text(
      "✓ Sequence complete!", timeout=timeout
    )

  def hooks_login(self, username: str = "admin", password: str = "password123") -> None:
    self.page.locator("#section-hooks").scroll_into_view_if_needed()
    self.page.locator("#hk-username").fill(username)
    self.page.locator("#hk-password").fill(password)
    self.page.locator("#hk-btn-login").click()
    expect(self.page.locator("#hk-main-section")).to_be_visible()

  def hooks_logout(self) -> None:
    self.page.locator("#hk-btn-logout").click()
    expect(self.page.locator("#hk-login-section")).to_be_visible()

  def hooks_create_record(self, name: str, category: str = "bug") -> None:
    self.page.locator("#hk-record-name").fill(name)
    self.page.locator("#hk-record-category").select_option(category)
    self.page.locator("#hk-btn-create").click()
    expect(self.page.locator("tr[data-record-id]")).to_have_count(1, timeout=5000)

  def hooks_delete_all_records(self) -> None:
    delete_buttons = self.page.locator("[id^='hk-btn-delete-']")
    while delete_buttons.count() > 0:
      delete_buttons.first.click()
    expect(self.page.locator("tr[data-record-id]")).to_have_count(0)
