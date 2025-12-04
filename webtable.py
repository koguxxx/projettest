import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/webtables"


def save_screenshot(driver, label: str) -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    path = os.path.join(desktop, f"{label}_{ts}.png")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        driver.save_screenshot(path)
        print(f"Saved screenshot: {path}")
    except Exception as e:
        print(f"Could not save screenshot: {e}")
    return path


def make_driver(headless: bool = False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    return drv


def open_page(driver):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "addNewRecordButton")))


def get_rows(driver):
    # Return visible data rows (skip header)
    body = driver.find_element(By.CLASS_NAME, "rt-tbody")
    rows = body.find_elements(By.CLASS_NAME, "rt-tr-group")
    # Filter out empty "No rows found" placeholders
    return [r for r in rows if r.text.strip() and "No rows found" not in r.text]


def find_row_by_text(driver, needle: str):
    for r in get_rows(driver):
        if needle.lower() in r.text.lower():
            return r
    return None


def click_add(driver):
    btn = driver.find_element(By.ID, "addNewRecordButton")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    btn.click()
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "registration-form-modal")))


def fill_form_and_submit(driver, first, last, email, age, salary, dept):
    set_field(driver, "firstName", first)
    set_field(driver, "lastName", last)
    set_field(driver, "userEmail", email)
    set_field(driver, "age", str(age))
    set_field(driver, "salary", str(salary))
    set_field(driver, "department", dept)
    driver.find_element(By.ID, "submit").click()
    # Wait modal to close
    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.ID, "registration-form-modal")))


def set_field(driver, fid, value):
    el = driver.find_element(By.ID, fid)
    el.clear()
    el.send_keys(value)
    return el


def click_row_action(row_el, title: str):
    # title is 'Edit' or 'Delete'
    btn = row_el.find_element(By.XPATH, ".//span[@title='{}']".format(title))
    btn.click()


def set_search(driver, query: str):
    box = driver.find_element(By.ID, "searchBox")
    box.clear()
    box.send_keys(query)
    # Wait for filter to apply
    time.sleep(0.5)


def set_page_size(driver, size: int):
    # Page size select
    sel = driver.find_element(By.CSS_SELECTOR, "select[aria-label='rows per page']")
    for opt in sel.find_elements(By.TAG_NAME, "option"):
        if opt.text.strip() == str(size):
            opt.click()
            break
    # Wait until table reflects new size (<= size rows visible)
    WebDriverWait(driver, 5).until(lambda d: len(get_rows(d)) <= size)


def get_column_values(driver, col_index: int) -> list[str]:
    vals = []
    for r in get_rows(driver):
        tds = r.find_elements(By.CLASS_NAME, "rt-td")
        if len(tds) > col_index:
            vals.append(tds[col_index].text.strip())
    return vals

def get_salary_numbers(driver) -> list[int]:
    raw = get_column_values(driver, 4)
    nums: list[int] = []
    for v in raw:
        try:
            if v:
                nums.append(int(v))
        except ValueError:
            continue
    return nums


def click_header(driver, header_text: str):
    hdr = driver.find_element(By.XPATH, f"//div[contains(@class,'rt-th')][.//div[text()='{header_text}']]")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hdr)
    hdr.click()
    time.sleep(0.5)


# WT01: Ajouter un enregistrement
def wt01_add_record(driver):
    open_page(driver)
    email = f"user{int(time.time())}@example.com"
    click_add(driver)
    fill_form_and_submit(driver, "Test", "User", email, 28, 7000, "QA")
    save_screenshot(driver, "webtables_wt01_after_add")
    row = find_row_by_text(driver, email)
    assert row is not None, "Newly added record should be visible in the table."


# WT02: Modifier un enregistrement
def wt02_edit_record(driver):
    open_page(driver)
    target = "Cierra"
    row = find_row_by_text(driver, target)
    if row is None:
        # If initial data changed, add a record to edit
        email = f"edit{int(time.time())}@example.com"
        click_add(driver)
        fill_form_and_submit(driver, "Edit", "Me", email, 35, 9000, "QA")
        row = find_row_by_text(driver, email)
    click_row_action(row, "Edit")
    # Change Department
    set_field(driver, "department", "Engineering")
    driver.find_element(By.ID, "submit").click()
    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.ID, "registration-form-modal")))
    save_screenshot(driver, "webtables_wt02_after_edit")
    # Verify department cell (col index 5) reflects change
    row = find_row_by_text(driver, "Engineering")
    assert row is not None, "Edited department should be visible immediately."


# WT03: Supprimer un enregistrement
def wt03_delete_record(driver):
    open_page(driver)
    # Add a disposable record to delete
    email = f"del{int(time.time())}@example.com"
    click_add(driver)
    fill_form_and_submit(driver, "To", "Delete", email, 30, 8000, "Ops")
    row = find_row_by_text(driver, email)
    assert row is not None, "Record to delete should exist first."
    click_row_action(row, "Delete")
    time.sleep(0.5)
    save_screenshot(driver, "webtables_wt03_after_delete")
    row2 = find_row_by_text(driver, email)
    assert row2 is None, "Deleted row should disappear from the table."


# WT04: Recherche par nom
def wt04_search_by_name(driver):
    open_page(driver)
    query = "Cierra"
    set_search(driver, query)
    save_screenshot(driver, "webtables_wt04_after_search")
    rows = get_rows(driver)
    assert len(rows) > 0, "Search should return at least one row for existing name."
    for r in rows:
        assert query.lower() in r.text.lower(), "Filter should only show matching results."


# WT05: Pagination à 5 lignes
def wt05_pagination_5_rows(driver):
    open_page(driver)
    # Ensure enough rows by adding if needed
    while len(get_rows(driver)) < 6:
        click_add(driver)
        idx = int(time.time()*1000) % 100000
        fill_form_and_submit(driver, f"User{idx}", "P5", f"p5_{idx}@ex.com", 25, 5000+idx%100, "Pag")
    set_page_size(driver, 5)
    rows = get_rows(driver)
    save_screenshot(driver, "webtables_wt05_after_pagination")
    assert 1 <= len(rows) <= 5, "Exactly up to 5 rows should be visible with page size 5."


# WT06: Trier la colonne Salary
def wt06_sort_salary(driver):
    open_page(driver)
    # Make sure there are some rows
    if len(get_rows(driver)) < 3:
        click_add(driver)
        fill_form_and_submit(driver, "Sort", "A", f"s{int(time.time())}@ex.com", 40, 6000, "HR")
    # Salary column index is 4 (0-based): [First, Last, Age, Email, Salary, Department, Action]
    # Click to sort ascending
    click_header(driver, "Salary")
    # Wait until ascending order is reflected
    WebDriverWait(driver, 5).until(lambda d: (lambda arr: len(arr) >= 2 and arr == sorted(arr))(get_salary_numbers(d)))
    asc_vals = get_salary_numbers(driver)
    save_screenshot(driver, "webtables_wt06_after_sort_asc")
    assert asc_vals == sorted(asc_vals), "Salary should be sorted ascending after first click."
    # Click again for descending
    click_header(driver, "Salary")
    WebDriverWait(driver, 5).until(lambda d: (lambda arr: len(arr) >= 2 and arr == sorted(arr, reverse=True))(get_salary_numbers(d)))
    desc_vals = get_salary_numbers(driver)
    save_screenshot(driver, "webtables_wt06_after_sort_desc")
    assert desc_vals == sorted(desc_vals, reverse=True), "Salary should be sorted descending after second click."


def main():
    failures = []
    tests = [
        ("WT01 add record", wt01_add_record),
        ("WT02 edit record", wt02_edit_record),
        ("WT03 delete record", wt03_delete_record),
        ("WT04 search by name", wt04_search_by_name),
        ("WT05 pagination 5 rows", wt05_pagination_5_rows),
        ("WT06 sort salary", wt06_sort_salary),
    ]
    for name, fn in tests:
        driver = None
        try:
            driver = make_driver(headless=False)
            fn(driver)
            print(f"PASS: {name}")
        except AssertionError as e:
            print(f"FAIL: {name} -> {e}")
            failures.append((name, str(e)))
        except Exception as e:
            print(f"ERROR: {name} -> {e}")
            failures.append((name, f"Unexpected: {e}"))
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

    if failures:
        print("\nSummary: Some tests failed")
        for name, msg in failures:
            print(f" - {name}: {msg}")
        sys.exit(1)
    else:
        print("\nSummary: All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    main()

