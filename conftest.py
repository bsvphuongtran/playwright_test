import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_html import extras

REPORTS_DIR = Path(__file__).parent / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
VIDEOS_DIR = REPORTS_DIR / "videos"

DEFAULT_APP_URL = "https://bsv-nhungnguyen.github.io/"


def pytest_configure(config: pytest.Config) -> None:
  SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
  VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict:
  return {"headless": True}


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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
  outcome = yield
  report = outcome.get_result()

  if report.when != "call":
    return

  page: Page | None = item.funcargs.get("page")
  if page is None or page.is_closed():
    return

  outcome_label = "passed" if report.passed else "failed" if report.failed else "skipped"
  test_name = _safe_name(item.name)
  screenshot_path = SCREENSHOTS_DIR / f"{test_name}_{outcome_label}.png"

  try:
    page.screenshot(path=str(screenshot_path), full_page=True)
  except Exception:
    screenshot_path = None

  video_path = None
  if report.failed:
    try:
      video_path = page.video.path() if page.video else None
    except Exception:
      video_path = None

  pytest_html = item.config.pluginmanager.getplugin("html")
  if pytest_html is not None and hasattr(report, "extra"):
    extra_items = []
    if screenshot_path and screenshot_path.exists():
      extra_items.append(
        extras.html(
          f'<div><a href="{screenshot_path.as_posix()}" target="_blank">'
          f"Screenshot ({outcome_label})</a></div>"
        )
      )
    if video_path:
      extra_items.append(
        extras.html(
          f'<div><a href="{video_path}" target="_blank">Video (failed)</a></div>'
        )
      )
    report.extra = getattr(report, "extra", []) + extra_items
