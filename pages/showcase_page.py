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
