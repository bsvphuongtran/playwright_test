import re

import pytest
from playwright.sync_api import Page, expect

from pages.showcase_page import ShowcasePage


class TestPlaywrightShowcase:
  @pytest.fixture(autouse=True)
  def setup(self, page: Page, app_url: str) -> None:
    self.page = page
    self.app = ShowcasePage(page, app_url)
    self.app.open()

  def test_Title(self) -> None:
    expect(
      self.page.get_by_role("heading", name="Playwright test 08.05.2026")
    ).to_be_visible()

  def test_Content(self) -> None:
    expect(
      self.page.get_by_text(
        "A playground for testing modern web automation strategies with Playwright. "
        "Explore complex DOM interactions, frames, and synchronization challenges."
      )
    ).to_be_visible()

  def test_Simple_Frame_Form(self) -> None:
    frame = self.app.demo_frame()
    frame.get_by_placeholder("Enter your name").fill("Test1")
    frame.get_by_role("button", name="Submit").click()
    expect(frame.locator("#frame-output")).to_have_text("✨ Success: Hello, Test1!")

  def test_Load_Nested_Frames_A_B_C(self) -> None:
    self.app.load_nested_frames()

  def test_Iframe_Alpha_Click_button(self) -> None:
    self.app.load_nested_frames()
    self.app.frame_alpha().get_by_role("button", name="Click button").click()
    expect(self.app.frame_alpha().locator("#res-A")).to_have_text("✨ Alpha Clicked!")

  def test_Iframe_Alpha_Open_Iframe_B(self) -> None:
    self.app.load_nested_frames()
    self.app.open_iframe_beta()

  def test_Iframe_Beta_Click_button(self) -> None:
    self.app.load_nested_frames()
    self.app.open_iframe_beta()
    self.app.frame_beta().get_by_role("button", name="Click button").click()
    expect(self.app.frame_beta().locator("#res-B")).to_have_text("✨ Beta Clicked!")

  def test_Iframe_Beta_Open_Iframe_C(self) -> None:
    self.app.load_nested_frames()
    self.app.open_iframe_beta()
    self.app.open_iframe_gamma()

  def test_Iframe_Gamma_Click_button(self) -> None:
    self.app.load_nested_frames()
    self.app.open_iframe_beta()
    self.app.open_iframe_gamma()
    self.app.frame_gamma().get_by_role("button", name="Click button").click()
    expect(self.app.frame_gamma().locator("#res-C")).to_have_text("✨ Gamma Clicked!")

  def test_Open_New_Tab(self) -> None:
    with self.page.expect_popup() as popup_info:
      self.page.get_by_role("button", name="Open New Tab (playwright.dev)").click()
    popup = popup_info.value
    popup.wait_for_load_state()
    expect(popup).to_have_url(re.compile(r"https://playwright\.dev/?"))

  def test_Open_Popup_Window(self) -> None:
    with self.page.expect_popup() as popup_info:
      self.page.get_by_role("button", name="Open Popup Window").click()
    popup = popup_info.value
    expect(popup.get_by_role("heading", name="Popup Activated")).to_be_visible()

  def test_Open_In_page_Modal(self) -> None:
    self.app.open_modal()
    expect(self.page.get_by_role("heading", name="Secure Confirmation")).to_be_visible()

  def test_Open_In_page_Modal_Cancel(self) -> None:
    self.app.open_modal()
    self.page.locator("#modal-cancel-btn").click()
    self.app.expect_modal_closed()

  def test_Open_In_page_Modal_Confirm(self) -> None:
    self.app.open_modal()
    self.page.locator("#modal-overlay").get_by_placeholder("Enter code (e.g. 1234)").fill("Test2")
    self.page.locator("#modal-confirm-btn").click()
    self.app.expect_modal_closed()
    expect(self.page.locator("#modal-result")).to_contain_text("✓ Verified: Test2")

  def test_Trigger_Alert(self) -> None:
    messages: list[str] = []

    def handle(dialog) -> None:
      messages.append(dialog.message)
      dialog.accept()

    self.page.once("dialog", handle)
    self.page.locator("#btn-alert").click()
    assert messages == ["⚠️ This is a browser alert!"]

  def test_Trigger_Alert_outside(self) -> None:
    def handle(dialog) -> None:
      assert dialog.message == "⚠️ This is a browser alert!"
      self.page.mouse.click(10, 10)
      dialog.accept()

    self.page.once("dialog", handle)
    self.page.locator("#btn-alert").click()

  def test_Trigger_Alert_OK(self) -> None:
    self.page.once("dialog", lambda dialog: dialog.accept())
    self.page.locator("#btn-alert").click()

  def test_Trigger_Confirm(self) -> None:
    captured: list = []

    def handle(dialog) -> None:
      captured.append(dialog)
      dialog.dismiss()

    self.page.once("dialog", handle)
    self.page.locator("#btn-confirm").click()
    assert captured[0].message == "Continue?"

  def test_Trigger_Confirm_outside(self) -> None:
    def handle(dialog) -> None:
      assert dialog.message == "Continue?"
      self.page.mouse.click(10, 10)
      dialog.dismiss()

    self.page.once("dialog", handle)
    self.page.locator("#btn-confirm").click()

  def test_Trigger_Confirm_Cancel(self) -> None:
    self.page.once("dialog", lambda dialog: dialog.dismiss())
    self.page.locator("#btn-confirm").click()
    expect(self.page.locator("#confirm-result")).to_contain_text("✗ Cancelled")

  def test_Trigger_Confirm_OK(self) -> None:
    self.page.once("dialog", lambda dialog: dialog.accept())
    self.page.locator("#btn-confirm").click()
    expect(self.page.locator("#confirm-result")).to_contain_text("✓ Confirmed")

  def test_Trigger_Prompt(self) -> None:
    captured: list = []

    def handle(dialog) -> None:
      captured.append(dialog)
      dialog.dismiss()

    self.page.once("dialog", handle)
    self.page.locator("#btn-prompt").click()
    assert captured[0].type == "prompt"

  def test_Trigger_Prompt_Cancel(self) -> None:
    self.page.once("dialog", lambda dialog: dialog.dismiss())
    self.page.locator("#btn-prompt").click()
    expect(self.page.locator("#prompt-result")).to_contain_text("Dismissed")

  def test_Trigger_Prompt_OK(self) -> None:
    self.page.once("dialog", lambda dialog: dialog.accept("Tester1"))
    self.page.locator("#btn-prompt").click()
    expect(self.page.locator("#prompt-result")).to_contain_text("👤 Name:")
    expect(self.page.locator("#prompt-result")).to_contain_text("Tester1")

  def test_Simulate_Failure_State(self) -> None:
    self.page.get_by_role("button", name="Simulate Failure State").click()
    expect(self.page.locator("#failure-msg")).to_contain_text("💥 CRITICAL FAILURE EMULATED")

  def test_Reset_State(self) -> None:
    self.page.get_by_role("button", name="Simulate Failure State").click()
    self.page.get_by_role("button", name="Reset State").click()
    expect(self.page.locator("#failure-msg")).to_have_text("System Normal")

  def test_Submit_Form_invalid1(self) -> None:
    self.page.locator("#trace-name").fill("")
    self.page.locator("#trace-email").fill("")
    self.page.get_by_role("button", name="Submit Form").click()
    expect(self.page.locator("#trace-result")).to_contain_text("⚠️ Both fields are required")

  def test_Submit_Form_invalid2(self) -> None:
    self.page.locator("#trace-name").fill("")
    self.page.locator("#trace-email").fill("test@gmail.com")
    self.page.get_by_role("button", name="Submit Form").click()
    expect(self.page.locator("#trace-result")).to_contain_text("⚠️ Both fields are required")

  def test_Submit_Form_invalid3(self) -> None:
    self.page.locator("#trace-name").fill("ABC")
    self.page.locator("#trace-email").fill("")
    self.page.get_by_role("button", name="Submit Form").click()
    expect(self.page.locator("#trace-result")).to_contain_text("⚠️ Both fields are required")

  def test_Submit_Form_valid(self) -> None:
    self.page.locator("#trace-name").fill("ABC")
    self.page.locator("#trace-email").fill("test@gmail.com")
    self.page.get_by_role("button", name="Submit Form").click()
    expect(self.page.locator("#trace-result")).to_contain_text("✓ Submitted: ABC")
