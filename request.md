You are a Senior QA Automation Engineer.
Your task is to generate and execute a complete Playwright Python automation project using POM (Page Object Model), based on test cases from an attached Excel/CSV file.
========================
INPUT
========================
- Test case file: C:\Users\ACER\AutoTesting\playwright_test\Playwright_Testcase.xlsx
- Column mapping:
  - 小項目 = test_name
  - 前提条件 = prerequisites
  - テスト手順 = steps
  - 期待する結果 = expected_result
- Target website URL:
  https://bsv-nhungnguyen.github.io/
- Generate tests for:
  Test-1 to Test-30
========================
GOALS
========================
1) Parse test cases into structured format:
   - test_name
   - prerequisites
   - steps
   - expected_result
2) Generate a complete runnable automation project
3) Keep architecture reusable for future test case files
4) Auto setup dependencies and execute tests
5) Produce HTML report with screenshot and video attachments for  FAILED tests
========================
MANDATORY PROJECT STRUCTURE
========================
project/
│
├── pages/
│   └── base_page.py 
│
├── tests/
│   └── playwright_test.py
│
├── conftest.py
├── pytest.ini
├── requirements.txt
├── automation_rules.md
│
└── .github/
    └── workflows/
        └── test.yml
========================
IMPLEMENTATION RULES
========================
[1] base_page.py (reusable methods required)
- click(selector)
- fill(selector, value)
- click_by_role(role, name)
- fill_by_placeholder(placeholder, value)
- expect_visible(selector)
- expect_not_visible(selector)
- expect_text(selector, text)
Locator strategy:
- Prefer user-facing locators first:
  - get_by_role
  - get_by_text
  - get_by_placeholder
- Avoid XPath unless absolutely necessary

[2] playwright_test.py (test style required)
- Use class-based style:
          ...
- Each test case = 1 pytest test method
- Tests independent
- Follow naming convention:
  test_<test_name>
- Example format:
  def test_Title(page: Page):
    expect(page.get_by_role("heading", name="寮情報管理")).to_be_visible()

[3] conftest.py requirements
- Fixture `app_url` (read APP_URL env, default to provided URL if needed)
- Force headless execution:
  browser_type_launch_args -> {"headless": True}
- Hook screenshot and video for fail in `pytest_runtest_makereport`
- Attach screenshot and video into pytest-html report links

[4] Report requirements
- Generate HTML report with pytest-html
- Include screenshot evidence for PASSED and FAILED
- Screenshot file naming should include test name + outcome

[5] requirements.txt
Must include at least:
- pytest
- playwright
- pytest-playwright
- pytest-html
- pandas
- openpyxl
- python-dotenv

[6] Auto-run setup and tests
After generating files, run commands automatically:
1. pip install -r requirements.txt
2. python -m playwright install chromium
3. pytest execution with APP_URL set to target URL
4. Return execution summary (total/passed/failed) and report path

[7] CI/CD workflow (.github/workflows/test.yml)
- Trigger: workflow_dispatch only
- Jobs:
  1. validate (install dependencies)
  2. run-tests (execute pytest)
  3. report (upload HTML report artifact)

========================
AUTOMATION RULE FILE (automation_rules.md)
========================
Must define:
- Coding conventions
- Locator strategy rules
- Naming conventions
- Test design principles
- POM structure rules
- Report evidence rules (pass/fail screenshot attachment)
- Headless execution rule
========================
OUTPUT FORMAT (STRICT)
========================
1) First: show parsed test cases (structured)
2) Then: generate ALL files with full code
3) Separate clearly by filename comments
4) Then execute setup + tests
5) Finally show:
   - Run command(s) used
   - Test summary
   - HTML report path
   - Screenshot folder path
========================
IMPORTANT RULES
========================
- DO NOT explain theory
- DO NOT skip files
- Code must be runnable
- Follow structure strictly
- If locator assumptions fail, inspect real DOM and adjust POM/tests accordingly
- Keep project reusable for future Excel/CSV files
