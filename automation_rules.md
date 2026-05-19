# Automation Rules

## Coding Conventions

- Python 3.11+ with type hints on shared helpers.
- Page objects live in `pages/`; tests live in `tests/`.
- Reuse `BasePage` helpers instead of duplicating Playwright calls in tests.
- One Excel row maps to one independent pytest method.

## Locator Strategy

1. Prefer user-facing locators: `get_by_role`, `get_by_text`, `get_by_placeholder`.
2. Use `#id` only when the testcase references a concrete element id.
3. Use `frame_locator` for iframe and nested iframe flows.
4. Avoid XPath unless no stable alternative exists.

## Naming Conventions

- Test classes: `Test<Feature>`.
- Test methods: `test_<sanitized_test_name>` (spaces and symbols become `_`).
- Screenshots: `{test_name}_{passed|failed|skipped}.png` under `reports/screenshots/`.
- Videos: stored under `reports/videos/` for failed runs.

## Test Design Principles

- Each test opens the app URL and sets up its own state.
- Prerequisites from Excel are implemented inside the test, not shared mutable state.
- Native dialogs use `page.expect_event("dialog")` and explicit `accept` / `dismiss`.
- Popups and new tabs use `page.expect_popup()`.

## POM Structure Rules

- `BasePage`: generic Playwright actions and assertions.
- Feature pages (for example `ShowcasePage`): section-specific flows and frame helpers.
- Tests should stay thin: arrange via page object, assert with `expect`.

## Report Evidence Rules

- HTML report generated with `pytest-html` at `reports/report.html`.
- Capture a full-page screenshot after every test call (passed and failed).
- Attach screenshot links to the HTML report.
- Attach video links for failed tests when browser video recording is available.

## Headless Execution Rule

- All local and CI runs must launch Chromium headless via `browser_type_launch_args = {"headless": True}`.
