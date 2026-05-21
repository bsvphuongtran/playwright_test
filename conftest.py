"""
Pytest + Playwright shared configuration.

Responsibilities:
- Provide the target application URL fixture.
- Force headless Chromium for all runs.
- On test failure: capture a focused screenshot and keep the session video
  (both use {TestName}_{yyyymmddHHMMSS}); attach them to the pytest-html report.
- On pass/skip: discard the recorded video so only failed runs leave artifacts.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, Page
from pytest_html import extras

# Output folders (created in pytest_configure).
REPORTS_DIR = Path(__file__).parent / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
VIDEOS_DIR = REPORTS_DIR / "videos"

# Fallback URL when APP_URL environment variable is not set.
DEFAULT_APP_URL = "https://bsv-nhungnguyen.github.io/"

# Maps each test name (without the "test_" prefix) to the DOM section that
# represents the main content under test. Used to crop screenshots to the
# relevant area instead of capturing the full page.
# Example: Simple_Frame_Form -> #section-iframe
TEST_FOCUS_SELECTORS: dict[str, str] = {
  "Title": "header",
  "Content": "header",
  "Simple_Frame_Form": "#section-iframe",
  "Load_Nested_Frames_A_B_C": "#section-iframe",
  "Iframe_Alpha_Click_button": "#section-iframe",
  "Iframe_Alpha_Open_Iframe_B": "#section-iframe",
  "Iframe_Beta_Click_button": "#section-iframe",
  "Iframe_Beta_Open_Iframe_C": "#section-iframe",
  "Iframe_Gamma_Click_button": "#section-iframe",
  "Open_New_Tab": "#section-windows",
  "Open_Popup_Window": "#section-windows",
  "Open_In_page_Modal": "#modal-overlay",
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
  # "Simulate_Failure_State": "#section-screenshot",
  # "Reset_State": "#section-screenshot",
  "Submit_Form_invalid1": "#section-tracing",
  "Submit_Form_invalid2": "#section-tracing",
  "Submit_Form_invalid3": "#section-tracing",
  "Submit_Form_valid": "#section-tracing",
}


def pytest_configure(config: pytest.Config) -> None:
  """Ensure report output directories exist before any test runs."""
  SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
  VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict:
  """Launch Chromium in headless mode (required for CI and local consistency)."""
  return {"headless": True}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
  """
  Record video per test so failures can be captured; passed tests delete
  their video in pytest_runtest_makereport (only failures are kept/renamed).
  """
  return {
    **browser_context_args,
    "record_video_dir": str(VIDEOS_DIR),
    "record_video_size": {"width": 1280, "height": 720},
  }


@pytest.fixture
def context(context: BrowserContext, request: pytest.FixtureRequest) -> BrowserContext:
  """
  Wrap pytest-playwright context teardown to remove videos for passed/skipped tests.
  Playwright writes the video file when the context closes, which happens after
  pytest_runtest_makereport — so deletion must run here, not in the makereport hook.
  """
  yield context
  rep = getattr(request.node, "rep_call", None)
  if rep is None or rep.failed:
    return
  _delete_recorded_videos(context)


@pytest.fixture
def app_url() -> str:
  """
  Base URL for the application under test.
  Override via APP_URL env var; otherwise uses DEFAULT_APP_URL.
  """
  return os.environ.get("APP_URL", DEFAULT_APP_URL).rstrip("/") + "/"


def _artifact_base_name(item_name: str) -> str:
  """
  Convert pytest node name to a clean artifact prefix.
  e.g. "test_Simple_Frame_Form[chromium]" -> "Simple_Frame_Form"
  """
  name = re.sub(r"\[.*\]$", "", item_name)  # strip parametrization suffix
  if name.startswith("test_"):
    name = name[5:]  # strip pytest method prefix
  return name


def _timestamp() -> str:
  """Return current time as yyyymmddHHMMSS for unique artifact filenames."""
  return datetime.now().strftime("%Y%m%d%H%M%S")


def _artifact_filename(item_name: str, extension: str, timestamp: str | None = None) -> str:
  """
  Build artifact filename: {TestName}_{yyyymmddHHMMSS}{extension}
  Example: Simple_Frame_Form_20260519150000.png
  """
  ts = timestamp or _timestamp()
  return f"{_artifact_base_name(item_name)}_{ts}{extension}"


def _capture_focused_screenshot(
  page: Page, item: pytest.Item, timestamp: str | None = None
) -> Path | None:
  """
  Capture a screenshot of the main test area (not full page).
  Falls back to viewport screenshot if the focus selector is missing/hidden.
  """
  base_name = _artifact_base_name(item.name)
  selector = TEST_FOCUS_SELECTORS.get(base_name, ".container")
  screenshot_path = SCREENSHOTS_DIR / _artifact_filename(item.name, ".png", timestamp)

  try:
    locator = page.locator(selector)
    if locator.count() > 0 and locator.first.is_visible():
      # Screenshot only the section element (focused content).
      locator.first.screenshot(path=str(screenshot_path))
    else:
      # Selector not visible — capture current viewport instead.
      page.screenshot(path=str(screenshot_path), full_page=False)
  except Exception:
    try:
      page.screenshot(path=str(screenshot_path), full_page=False)
    except Exception:
      return None

  return screenshot_path if screenshot_path.exists() else None


def _delete_recorded_videos(context: BrowserContext) -> None:
  """Delete Playwright session videos after a passed or skipped test."""
  for page in list(context.pages):
    try:
      if page.video is None:
        continue
      if not page.is_closed():
        page.close()
      video_path = page.video.path()
      if video_path and Path(video_path).exists():
        Path(video_path).unlink()
    except Exception:
      pass


def _save_failed_video(page: Page, item: pytest.Item, timestamp: str) -> Path | None:
  """
  Close the page so Playwright flushes the video file, then move it to
  reports/videos/ using the same naming format as screenshots.
  Example: Simple_Frame_Form_20260519150000.webm
  """
  if page.video is None:
    return None

  video_dest = VIDEOS_DIR / _artifact_filename(item.name, ".webm", timestamp)

  try:
    if not page.is_closed():
      page.close()  # required before video.path() returns the final file
    source = page.video.path()
    if not source:
      return None
    source_path = Path(source)
    if source_path.exists():
      shutil.move(str(source_path), video_dest)
      return video_dest if video_dest.exists() else None
  except Exception:
    return None

  return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
  """
  Pytest hook that runs after each test phase (setup/call/teardown).

  After the *call* phase:
  - Failed: focused screenshot + video kept as {TestName}_{yyyymmddHHMMSS}.*
  - Passed/skipped: video discarded (no screenshot)
  - Failed only: attach screenshot/video links to pytest-html report
  """
  outcome = yield
  report = outcome.get_result()

  # Store report on the item so other hooks/fixtures can read test outcome.
  setattr(item, f"rep_{report.when}", report)

  if report.when != "call":
    return

  if not report.failed:
    return

  page: Page | None = item.funcargs.get("page")
  if page is None:
    return

  # Shared timestamp so screenshot and video for the same failure match.
  artifact_ts = _timestamp()

  screenshot_path = None
  if not page.is_closed():
    screenshot_path = _capture_focused_screenshot(page, item, artifact_ts)

  video_path = _save_failed_video(page, item, artifact_ts)

  pytest_html = item.config.pluginmanager.getplugin("html")
  if pytest_html is None or not hasattr(report, "extra"):
    return

  extra_items: list = []
  if screenshot_path:
    # Relative path so links work from reports/report.html.
    rel = screenshot_path.relative_to(REPORTS_DIR).as_posix()
    extra_items.append(
      extras.html(
        f'<div><a href="{rel}" target="_blank">Screenshot (failed): {screenshot_path.name}</a></div>'
      )
    )
    extra_items.append(extras.image(str(screenshot_path)))

  if video_path:
    rel = video_path.relative_to(REPORTS_DIR).as_posix()
    extra_items.append(
      extras.html(
        f'<div><a href="{rel}" target="_blank">Video (failed): {video_path.name}</a></div>'
      )
    )

  report.extra = getattr(report, "extra", []) + extra_items
