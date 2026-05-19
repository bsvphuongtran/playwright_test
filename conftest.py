import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_html import extras

REPORTS_DIR = Path(__file__).parent / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
VIDEOS_DIR = REPORTS_DIR / "videos"

DEFAULT_APP_URL = "https://bsv-nhungnguyen.github.io/"

# Main UI area per testcase (scroll + clip capture / video viewport focus)
FOCUS_SELECTORS: dict[str, str] = {
  "Title": "header",
  "Content": "header",
  "Simple_Frame_Form": "#section-iframe",
  "Load_Nested_Frames_A_B_C": "#section-iframe",
  "Iframe_Alpha_Click_button": "#iframe-A",
  "Iframe_Alpha_Open_Iframe_B": "#iframe-A",
  "Iframe_Beta_Click_button": "#iframe-A",
  "Iframe_Beta_Open_Iframe_C": "#iframe-A",
  "Iframe_Gamma_Click_button": "#iframe-A",
  "Open_New_Tab": "#section-windows",
  "Open_Popup_Window": "#section-windows",
  "Open_In_page_Modal": "#section-windows",
  "Open_In_page_Modal_Cancel": "#modal-overlay",
  "Open_In_page_Modal_Confirm": "#modal-overlay",
  "Trigger_Alert": "#section-dialogs",
  "Trigger_Alert_outside": "#section-dialogs",
  "Trigger_Alert_OK": "#section-dialogs",
  "Trigger_Confirm": "#section-dialogs",
  "Trigger_Confirm_outside": "#section-dialogs",
  "Trigger_Confirm_Cancel": "#section-dialogs",
  "Trigger_Confirm_OK": "#section-dialogs",
  "Trigger_Prompt": "#section-dialogs",
  "Trigger_Prompt_Cancel": "#section-dialogs",
  "Trigger_Prompt_OK": "#section-dialogs",
  "Simulate_Failure_State": "#section-screenshot",
  "Reset_State": "#section-screenshot",
  "Submit_Form_invalid1": "#section-tracing",
  "Submit_Form_invalid2": "#section-tracing",
  "Submit_Form_invalid3": "#section-tracing",
  "Submit_Form_valid": "#section-tracing",
}

DEFAULT_FOCUS = ".container"
SLOW_MO_MS = 500


def pytest_configure(config: pytest.Config) -> None:
  SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
  VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict:
  return {"headless": True, "slow_mo": SLOW_MO_MS}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
  return {
    **browser_context_args,
    "record_video_dir": str(VIDEOS_DIR),
    "record_video_size": {"width": 1280, "height": 720},
  }


@pytest.fixture
def app_url() -> str:
  return os.environ.get("APP_URL", DEFAULT_APP_URL).rstrip("/") + "/"


def _safe_name(name: str) -> str:
  return re.sub(r"[^\w\-]+", "_", name).strip("_")


def _test_base_name(item: pytest.Item) -> str:
  name = item.name.split("[", 1)[0]
  if name.startswith("test_"):
    name = name[5:]
  return _safe_name(name)


def _timestamp() -> str:
  return datetime.now().strftime("%Y%m%d%H%M%S")


def _discard_pass_video(page: Page) -> None:
  try:
    if page.video and not page.is_closed():
      page.close()
    if page.video:
      raw = page.video.path()
      if raw and Path(raw).exists():
        Path(raw).unlink()
  except Exception:
    pass


def _focus_locator(page: Page, test_base: str):
  selector = FOCUS_SELECTORS.get(test_base, DEFAULT_FOCUS)
  locator = page.locator(selector).first
  locator.scroll_into_view_if_needed(timeout=10_000)
  return locator


@pytest.fixture(autouse=True)
def focus_main_test_content(request: pytest.FixtureRequest, page: Page) -> None:
  """Scroll the viewport to the section under test before each step (slow-mo video)."""
  test_base = _test_base_name(request.node)
  try:
    _focus_locator(page, test_base)
  except Exception:
    pass
  yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
  outcome = yield
  report = outcome.get_result()

  if report.when != "call":
    return

  page: Page | None = item.funcargs.get("page")
  if page is None:
    return

  if report.passed:
    _discard_pass_video(page)
    return

  if not report.failed:
    return

  test_base = _test_base_name(item)
  stamp = _timestamp()
  screenshot_path: Path | None = None
  video_path: Path | None = None

  try:
    focus = _focus_locator(page, test_base)
    screenshot_path = SCREENSHOTS_DIR / f"{test_base}_{stamp}.png"
    focus.screenshot(path=str(screenshot_path))
  except Exception:
    screenshot_path = None

  try:
    if page.video and not page.is_closed():
      page.close()
    if page.video:
      raw_video = page.video.path()
      if raw_video:
        video_path = VIDEOS_DIR / f"{test_base}_{stamp}.webm"
        shutil.move(str(raw_video), str(video_path))
  except Exception:
    video_path = None

  pytest_html = item.config.pluginmanager.getplugin("html")
  if pytest_html is None or not hasattr(report, "extra"):
    return

  extra_items: list = []
  if screenshot_path and screenshot_path.exists():
    rel = screenshot_path.relative_to(REPORTS_DIR)
    extra_items.append(
      extras.html(
        f'<div><a href="{rel.as_posix()}" target="_blank">'
        f"Screenshot: {screenshot_path.name}</a></div>"
      )
    )
  if video_path and video_path.exists():
    rel = video_path.relative_to(REPORTS_DIR)
    extra_items.append(
      extras.html(
        f'<div><a href="{rel.as_posix()}" target="_blank">'
        f"Video: {video_path.name}</a></div>"
      )
    )
  report.extra = getattr(report, "extra", []) + extra_items
