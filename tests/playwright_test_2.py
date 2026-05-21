import re

import pytest
from playwright.sync_api import FrameLocator, Page, expect

BASE_URL = "https://bsv-nhungnguyen.github.io/"

@pytest.fixture(autouse=True)
def open_page(page: Page)-> None:
    page.goto(BASE_URL)

#================TESTCASES================

def test_Title(page: Page)-> None:
    expect(
      page.get_by_role("heading", name="Playwright test 08.05.2026")
    ).to_be_visible()

def test_Content(page: Page)-> None:
    expect(
      page.get_by_text(
        "A playground for testing modern web automation strategies with Playwright. "
        "Explore complex DOM interactions, frames, and synchronization challenges."
      )
    ).to_be_visible()

def test_Simple_Frame_Form(page: Page)-> None:
    frame = page.frame_locator("#demo-iframe")
    frame.get_by_placeholder("Enter your name").fill("Test1")
    frame.get_by_role("button", name="Submit").click()
    expect(frame.locator("#frame-output")).to_have_text("Success: Hello Test1!")

def test_Load_Nested_Frames_A_B_C(page: Page)-> None:
    page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    frame_alpha = page.frame_locator("#iframe-A")
    expect(frame_alpha.get_by_text("Iframe A")).to_be_visible()

def test_Iframe_Alpha_Click_button(page: Page)-> None:
    page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    frame_alpha = page.frame_locator("#iframe-A")
    frame_alpha.get_by_role("button", name="Click button").click()
    expect(frame_alpha.locator("#res-A")).to_have_text("Iframe A Clicked!")

def test_Iframe_Alpha_Open_Iframe_B(page: Page) -> None:
    page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    frame_alpha = page.frame_locator("#iframe-A")
    frame_alpha.get_by_role("button", name="Open Iframe B").click()
    frame_beta = frame_alpha.frame_locator("#iframe-B")
    expect(frame_beta.get_by_text("Iframe B")).to_be_visible()

def test_Iframe_Beta_Click_button(page: Page)-> None:
    page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    frame_alpha = page.frame_locator("#iframe-A")
    frame_alpha.get_by_role("button", name="Open Iframe B").click()
    frame_beta = frame_alpha.frame_locator("#iframe-B")
    frame_beta.get_by_role("button", name="Click button").click()
    expect(frame_beta.locator("#res-B")).to_have_text("Iframe B Clicked!")

def test_Iframe_Beta_Open_Iframe_C(page: Page):
    page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    frame_alpha = page.frame_locator("#iframe-A")
    frame_alpha.get_by_role("button", name="Open Iframe B").click()
    frame_beta = frame_alpha.frame_locator("#iframe-B")
    frame_beta.get_by_role("button", name="Open Iframe C").click()
    frame_gamma = frame_beta.frame_locator("#iframe-C")
    expect(frame_gamma.get_by_text("Iframe C")).to_be_visible()

def test_Iframe_Gamma_Click_button(page: Page):
    page.get_by_role("button", name="Load Nested Frames (A → B → C)").click()
    frame_alpha = page.frame_locator("#iframe-A")
    frame_alpha.get_by_role("button", name="Open Iframe B").click()
    frame_beta = frame_alpha.frame_locator("#iframe-B")
    frame_beta.get_by_role("button", name="Open Iframe C").click()
    frame_gamma = frame_beta.frame_locator("#iframe-C")
    frame_gamma.get_by_role("button", name="Click button").click()
    expect(frame_gamma.locator("#res-C")).to_have_text("Iframe C Clicked!")

def test_Open_New_Tab(page: Page) -> None:
    with page.expect_popup() as tab_info:
      page.get_by_role("button", name="Open New Tab (playwright.dev)").click()
    new_tab = tab_info.value
    new_tab.wait_for_load_state()
    expect(new_tab).to_have_url(re.compile(r"https://playwright\.dev/?"))

def test_Open_Popup_Window(page: Page) -> None:
    with page.expect_popup() as popup_info:
      page.get_by_role("button", name="Open Popup Window").click()
    popup = popup_info.value
    expect(popup.get_by_role("heading", name="Popup Activated")).to_be_visible()

def test_Open_In_page_Modal(page: Page) -> None:
    page.get_by_role("button", name="Open In-page Modal").click()
    #expect(page.locator("#modal-overlay.active")).to_be_visible()
    expect(page.get_by_role("heading", name="Secure Confirmation")).to_be_visible()

def test_Open_In_page_Modal_Cancel(page: Page) -> None:
    page.get_by_role("button", name="Open In-page Modal").click()
    #expect(page.locator("#modal-overlay.active")).to_be_visible()
    page.locator("#modal-cancel-btn").click()
    expect(page.locator("#modal-overlay.active")).not_to_be_visible()

def test_Open_In_page_Modal_Confirm(page: Page) -> None:
    page.get_by_role("button", name="Open In-page Modal").click()
    #expect(page.locator("#modal-overlay.active")).to_be_visible()
    page.locator("#modal-overlay").get_by_placeholder("Enter code (e.g. 1234)").fill("Test2")
    page.locator("#modal-confirm-btn").click()
    expect(page.locator("#modal-overlay.active")).not_to_be_visible()
    expect(page.locator("#modal-result")).to_contain_text("✓ Verified: Test2")

def test_Trigger_Alert(page: Page) -> None:
    alert: list[str] = []

    def handle(dialog) -> None:
      alert.append(dialog.message)
      dialog.accept()

    page.once("dialog", handle)
    page.locator("#btn-alert").click()
    assert alert == ["This is a browser alert!"]

def test_Trigger_Alert_outside(page: Page) -> None:
    def handle(dialog) -> None:
      assert dialog.message == "This is a browser alert!"
      page.mouse.click(10, 10)
      dialog.accept()

    page.once("dialog", handle)
    page.locator("#btn-alert").click()

def test_Trigger_Alert_OK(page: Page) -> None:
    page.once("dialog", lambda dialog: dialog.accept())

    page.locator("#btn-alert").click()

def test_Trigger_Confirm(page: Page) -> None:
    captured: list = []

    def handle(dialog) -> None:
      captured.append(dialog)
      dialog.dismiss()

    page.once("dialog", handle)
    page.locator("#btn-confirm").click()
    assert captured[0].message == "Continue?"

def test_Trigger_Confirm_outside(page: Page) -> None:
    def handle(dialog) -> None:
      assert dialog.message == "Continue?"
      page.mouse.click(10, 10)
      dialog.dismiss()

    page.once("dialog", handle)
    page.locator("#btn-confirm").click()

def test_Trigger_Confirm_Cancel(page: Page) -> None:
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("#btn-confirm").click()
    expect(page.locator("#confirm-result")).to_contain_text("✗ Cancelled")

def test_Trigger_Confirm_OK(page: Page) -> None:
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#btn-confirm").click()
    expect(page.locator("#confirm-result")).to_contain_text("✓ Confirmed")


def test_Trigger_Prompt(page: Page) -> None:
    captured: list = []

    def handle(dialog) -> None:
      captured.append(dialog)
      dialog.dismiss()

    page.once("dialog", handle)
    page.locator("#btn-prompt").click()
    assert captured[0].type == "prompt"

def test_Trigger_Prompt_Cancel(page: Page) -> None:
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("#btn-prompt").click()
    expect(page.locator("#prompt-result")).to_contain_text("Dismissed")

def test_Trigger_Prompt_OK(page: Page) -> None:
    page.once("dialog", lambda dialog: dialog.accept("Tester1"))
    page.locator("#btn-prompt").click()
    expect(page.locator("#prompt-result")).to_contain_text("Name:")
    expect(page.locator("#prompt-result")).to_contain_text("Tester1")


def test_Submit_Form_invalid1(page: Page) -> None:
    page.locator("#trace-name").fill("")
    page.locator("#trace-email").fill("")
    page.get_by_role("button", name="Submit Form").click()
    expect(page.locator("#trace-result")).to_contain_text("Both fields are required")

def test_Submit_Form_invalid2(page: Page) -> None:
    page.locator("#trace-name").fill("")
    page.locator("#trace-email").fill("test@gmail.com")
    page.get_by_role("button", name="Submit Form").click()
    expect(page.locator("#trace-result")).to_contain_text("Both fields are required")

def test_Submit_Form_invalid3(page: Page) -> None:
    page.locator("#trace-name").fill("ABC")
    page.locator("#trace-email").fill("")
    page.get_by_role("button", name="Submit Form").click()
    expect(page.locator("#trace-result")).to_contain_text("Both fields are required")

def test_Submit_Form_valid(page: Page) -> None:
    page.locator("#trace-name").fill("ABC")
    page.locator("#trace-email").fill("test@gmail.com")
    page.get_by_role("button", name="Submit Form").click()
    expect(page.locator("#trace-result")).to_contain_text("✓ Submitted: ABC")


