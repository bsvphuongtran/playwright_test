from playwright.sync_api import Page, expect


class BasePage:
  def __init__(self, page: Page) -> None:
    self.page = page

  def click(self, selector: str) -> None:
    self.page.locator(selector).click()

  def fill(self, selector: str, value: str) -> None:
    self.page.locator(selector).fill(value)

  def click_by_role(self, role: str, name: str) -> None:
    self.page.get_by_role(role, name=name).click()

  def fill_by_placeholder(self, placeholder: str, value: str) -> None:
    self.page.get_by_placeholder(placeholder).fill(value)

  def expect_visible(self, selector: str) -> None:
    expect(self.page.locator(selector)).to_be_visible()

  def expect_not_visible(self, selector: str) -> None:
    expect(self.page.locator(selector)).not_to_be_visible()

  def expect_text(self, selector: str, text: str) -> None:
    expect(self.page.locator(selector)).to_contain_text(text)
