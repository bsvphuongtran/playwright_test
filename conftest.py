"""
Pytest + Playwright shared configuration.

Media rules:
- Default: no video recording (avoids orphan page@*.webm files).
- On FAILED: screenshot + video only for tests in FAIL_MEDIA_TESTS.
- On PASSED: screenshot + video only for tests in PASS_MEDIA_TESTS (e.g. Element_Video).
- Full_Page_Screenshot: screenshot on pass via PASS_SCREENSHOT_TESTS.
"""

import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, Page
from pytest_html import extras

REPORTS_DIR = Path(__file__).parent / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
VIDEOS_DIR = REPORTS_DIR / "videos"
TRACES_DIR = REPORTS_DIR / "traces"

DEFAULT_APP_URL = "https://bsv-nhungnguyen.github.io/"

# Tests that enable Playwright context video recording (required to capture anything).
TESTS_WITH_VIDEO_RECORDING = {
  "Element_Video",
  "Element_Video_Failed",
  "Element_Screenshot_Failed",
}

# On PASSED: keep screenshot + video (Excel #32 – video in all outcomes).
PASS_MEDIA_TESTS = {"Element_Video"}

# On PASSED: keep screenshot only (Excel #29 – screenshot in all outcomes).
PASS_SCREENSHOT_TESTS = {"Full_Page_Screenshot"}

# On FAILED: keep screenshot + video.
FAIL_MEDIA_TESTS = {
  "Element_Video",
  "Element_Screenshot_Failed",
  "Element_Video_Failed",
}

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
  "Submit_Form_invalid1": "#section-tracing",
  "Submit_Form_invalid2": "#section-tracing",
  "Submit_Form_invalid3": "#section-tracing",
  "Submit_Form_valid": "#section-tracing",
  "Full_Page_Screenshot": "#section-screenshot",
  "Element_Screenshot_Pass": "#screenshot-element",
  "Element_Screenshot_Failed": "#section-screenshot",
  "Element_Video": "#section-screenshot",
  "Element_Video_Pass": "#section-screenshot",
  "Element_Video_Failed": "#section-screenshot",
  "Tracing": "#section-tracing",
  "Tracing_Failed_OK": "#section-tracing",
  "Tracing_Failed_NG": "#section-tracing",
  "beforeAll": ".container",
  "afterAll": "#section-hooks",
  "beforeEach": "#section-hooks",
  "afterEach": "#section-hooks",
}

TRACE_MODES: dict[str, str] = {
  "Tracing": "always",
  "Tracing_Failed": "fail_only",
}


def pytest_configure(config: pytest.Config) -> None:
  SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
  VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
  TRACES_DIR.mkdir(parents=True, exist_ok=True)
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def pytest_sessionstart(session: pytest.Session) -> None:
  print(f"\n[beforeAll] Screenshot folder: {SCREENSHOTS_DIR.resolve()}")
  print(f"[beforeAll] Video folder (whitelist only): {VIDEOS_DIR.resolve()}")
  print(f"[beforeAll] Trace folder: {TRACES_DIR.resolve()}")
  _cleanup_orphan_videos()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
  if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
  print("\n[afterAll] Kết thúc test session – dọn dẹp môi trường")
  _cleanup_orphan_videos()


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict:
  return {"headless": True}


@pytest.fixture
def browser_context_args(
  browser_context_args: dict, request: pytest.FixtureRequest
) -> dict:
  """
  Enable video recording only for tests that need pass/fail media artifacts.
  All other tests run without record_video_dir (no stray videos).
  """
  test_name = _artifact_base_name(request.node.name)
  if test_name not in TESTS_WITH_VIDEO_RECORDING:
    return browser_context_args

  return {
    **browser_context_args,
    "record_video_dir": str(VIDEOS_DIR),
    "record_video_size": {"width": 1280, "height": 720},
  }


@pytest.fixture
def context(context: BrowserContext, request: pytest.FixtureRequest) -> BrowserContext:
  """
  After the test: save playable video via save_as() or delete raw recording.
  Video must be finalized here (after page close), not in pytest_runtest_makereport.
  """
  yield context

  test_name = _artifact_base_name(request.node.name)
  if test_name not in TESTS_WITH_VIDEO_RECORDING:
    return

  rep = getattr(request.node, "rep_call", None)
  if rep is None:
    _delete_recorded_videos(context)
    return

  if _should_keep_video(test_name, rep.failed, rep.passed):
    timestamp = getattr(request.node, "_artifact_ts", None) or _timestamp()
    video_path = _save_context_video(context, request.node, timestamp)
    if video_path:
      request.node.saved_video_path = video_path
    return

  _delete_recorded_videos(context)


@pytest.fixture(autouse=True)
def manage_tracing(context: BrowserContext, request: pytest.FixtureRequest) -> None:
  test_name = _artifact_base_name(request.node.name)
  mode = TRACE_MODES.get(test_name)
  if mode is None:
    yield
    return

  context.tracing.start(screenshots=True, snapshots=True, sources=True)
  yield

  rep = getattr(request.node, "rep_call", None)
  trace_path = TRACES_DIR / _artifact_filename(request.node.name, ".zip")
  should_save = mode == "always" or (mode == "fail_only" and rep is not None and rep.failed)

  if should_save:
    context.tracing.stop(path=str(trace_path))
    request.node.trace_path = trace_path
    assert trace_path.exists()
    assert trace_path.stat().st_size > 0
  else:
    context.tracing.stop()


@pytest.fixture
def app_url() -> str:
  return os.environ.get("APP_URL", DEFAULT_APP_URL).rstrip("/") + "/"


def _artifact_base_name(item_name: str) -> str:
  name = re.sub(r"\[.*\]$", "", item_name)
  if name.startswith("test_"):
    name = name[5:]
  return name


def _timestamp() -> str:
  return datetime.now().strftime("%Y%m%d%H%M%S")


def _artifact_filename(item_name: str, extension: str, timestamp: str | None = None) -> str:
  ts = timestamp or _timestamp()
  return f"{_artifact_base_name(item_name)}_{ts}{extension}"


def _capture_focused_screenshot(
  page: Page, item: pytest.Item, timestamp: str | None = None
) -> Path | None:
  base_name = _artifact_base_name(item.name)
  selector = TEST_FOCUS_SELECTORS.get(base_name, ".container")
  screenshot_path = SCREENSHOTS_DIR / _artifact_filename(item.name, ".png", timestamp)

  try:
    locator = page.locator(selector)
    if locator.count() > 0 and locator.first.is_visible():
      locator.first.screenshot(path=str(screenshot_path))
    else:
      page.screenshot(path=str(screenshot_path), full_page=False)
  except Exception:
    try:
      page.screenshot(path=str(screenshot_path), full_page=False)
    except Exception:
      return None

  return screenshot_path if screenshot_path.exists() else None


def _wait_for_video_file(path: Path, timeout: float = 10.0) -> bool:
  """Wait until Playwright finishes writing a non-empty WebM file."""
  deadline = time.monotonic() + timeout
  last_size = -1
  stable_checks = 0

  while time.monotonic() < deadline:
    if path.exists():
      size = path.stat().st_size
      if size > 0 and size == last_size:
        stable_checks += 1
        if stable_checks >= 2:
          return True
      else:
        stable_checks = 0
        last_size = size
    time.sleep(0.2)

  return path.exists() and path.stat().st_size > 0


def _delete_recorded_videos(context: BrowserContext) -> None:
  for page in list(context.pages):
    try:
      if page.video is None:
        continue
      if not page.is_closed():
        page.close()
      video_path = Path(page.video.path())
      if _wait_for_video_file(video_path):
        video_path.unlink()
    except Exception:
      pass


def _cleanup_orphan_videos() -> None:
  """Remove Playwright raw video files that were not renamed."""
  if not VIDEOS_DIR.exists():
    return
  for path in VIDEOS_DIR.glob("*.webm"):
    is_raw_video = path.name.startswith("page@") or re.fullmatch(
      r"[0-9a-f]{32}\.webm", path.name
    )
    if not is_raw_video:
      continue
    try:
      path.unlink()
    except Exception:
      pass


def _should_keep_video(test_name: str, failed: bool, passed: bool) -> bool:
  if failed and test_name in FAIL_MEDIA_TESTS:
    return True
  if passed and test_name in PASS_MEDIA_TESTS:
    return True
  return False


def _save_context_video(context: BrowserContext, item: pytest.Item, timestamp: str) -> Path | None:
  """
  Close the page first so Playwright finalizes the WebM, then move the raw
  recording to its test artifact name.
  """
  video_dest = VIDEOS_DIR / _artifact_filename(item.name, ".webm", timestamp)

  for page in list(context.pages):
    if page.video is None:
      continue
    try:
      if not page.is_closed():
        page.close()
      source = Path(page.video.path())
      if not _wait_for_video_file(source):
        continue
      if video_dest.exists():
        video_dest.unlink()
      shutil.move(str(source), str(video_dest))
      if _wait_for_video_file(video_dest):
        _cleanup_orphan_videos()
        return video_dest
    except Exception:
      pass
  return None


def _attach_media_to_report(
  report: pytest.TestReport,
  screenshot_path: Path | None,
  video_path: Path | None,
  label: str,
) -> None:
  extra_items: list = []
  if screenshot_path:
    rel = screenshot_path.relative_to(REPORTS_DIR).as_posix()
    extra_items.append(
      extras.html(
        f'<div><a href="{rel}" target="_blank">Screenshot ({label}): '
        f"{screenshot_path.name}</a></div>"
      )
    )
    extra_items.append(extras.image(str(screenshot_path)))

  if video_path:
    rel = video_path.relative_to(REPORTS_DIR).as_posix()
    extra_items.append(
      extras.html(
        f'<div><a href="{rel}" target="_blank">Video ({label}): {video_path.name}</a></div>'
        f'<video controls width="640" style="max-width:100%;margin-top:8px;">'
        f'<source src="{rel}" type="video/webm"></video>'
      )
    )

  if extra_items:
    report.extra = getattr(report, "extra", []) + extra_items


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
  outcome = yield
  report = outcome.get_result()
  setattr(item, f"rep_{report.when}", report)

  if report.when == "teardown":
    video_path = getattr(item, "saved_video_path", None)
    call_report = getattr(item, "rep_call", None)
    if video_path and call_report:
      label = "failed" if call_report.failed else "passed"
      _attach_media_to_report(call_report, None, video_path, label)
    return

  if report.when != "call":
    return

  page: Page | None = item.funcargs.get("page")
  if page is None:
    return

  test_name = _artifact_base_name(item.name)
  artifact_ts = _timestamp()
  item._artifact_ts = artifact_ts

  if not report.failed:
    if test_name in PASS_MEDIA_TESTS:
      screenshot_path = (
        _capture_focused_screenshot(page, item, artifact_ts) if not page.is_closed() else None
      )
      _attach_media_to_report(report, screenshot_path, None, "passed")
    elif test_name in PASS_SCREENSHOT_TESTS:
      screenshot_path = (
        _capture_focused_screenshot(page, item, artifact_ts) if not page.is_closed() else None
      )
      _attach_media_to_report(report, screenshot_path, None, "passed")
    return

  if test_name in FAIL_MEDIA_TESTS and not page.is_closed():
    screenshot_path = _capture_focused_screenshot(page, item, artifact_ts)
    if screenshot_path:
      _attach_media_to_report(report, screenshot_path, None, "failed")
