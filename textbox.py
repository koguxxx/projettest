import sys
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

URL = "https://demoqa.com/text-box"


def make_driver(headless: bool = False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Selenium Manager (built into Selenium 4.6+) will resolve the driver automatically
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    return drv


def open_page(driver):
    driver.get(URL)


def fill_common_fields(driver, name="Mohamed Test", current="Addr 1", permanent="Addr 2"):
    driver.find_element(By.ID, "userName").clear()
    driver.find_element(By.ID, "userName").send_keys(name)
    driver.find_element(By.ID, "currentAddress").clear()
    driver.find_element(By.ID, "currentAddress").send_keys(current)
    driver.find_element(By.ID, "permanentAddress").clear()
    driver.find_element(By.ID, "permanentAddress").send_keys(permanent)


def set_email(driver, value: str):
    el = driver.find_element(By.ID, "userEmail")
    el.clear()
    if value is not None:
        el.send_keys(value)
    return el


def submit(driver, label: str | None = None):
    btn = driver.find_element(By.ID, "submit")
    # Scroll into view to avoid footer overlay
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "submit")))
        btn.click()
    except Exception:
        # Fallback to JS click if intercepted
        driver.execute_script("arguments[0].click();", btn)
    # Wait for results to show, then capture screenshot if requested
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "output")))
    finally:
        if label:
            save_screenshot(driver, label)


def get_output_text(driver) -> str:
    try:
        el = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "output"))
        )
        return el.text
    except Exception:
        return ""


def save_screenshot(driver, label: str) -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    path = os.path.join(desktop, f"{label}_{ts}.png")
    try:
        # Ensure directory exists (Desktop should exist, but guard anyway)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        driver.save_screenshot(path)
        print(f"Saved screenshot: {path}")
    except Exception as e:
        print(f"Could not save screenshot: {e}")
    return path


def has_error_class(element) -> bool:
    cls = element.get_attribute("class") or ""
    return "field-error" in cls.split()


def test_valid_email(driver):
    email = "mohamed.cherif02@esprit.tn"
    open_page(driver)
    fill_common_fields(driver)
    email_input = set_email(driver, email)
    submit(driver, label="valid_email_after_submit")

    assert not has_error_class(email_input), "Valid email should not have 'field-error'."
    out = get_output_text(driver)
    assert "Email:" in out and email in out, "Output should include the valid email."


def test_empty_email(driver):
    open_page(driver)
    fill_common_fields(driver)
    email_input = set_email(driver, "")
    submit(driver, label="empty_email_after_submit")

    assert not has_error_class(email_input), "Empty email should not be marked as error."
    out = get_output_text(driver)
    assert "Email:" not in out, "Email line should be absent for empty email."


def test_invalid_email(driver):
    bad_email = "mohamed.cherifesprit.tn"
    open_page(driver)
    fill_common_fields(driver)
    email_input = set_email(driver, bad_email)
    submit(driver, label="invalid_email_after_submit")

    assert has_error_class(email_input), "Invalid email should have 'field-error'."
    out = get_output_text(driver)
    assert "Email:" not in out, "Email line should not be present for invalid email."


def test_invalid_email_missing_domain(driver):
    bad_email = "mohamed.cherif02@"
    open_page(driver)
    fill_common_fields(driver)
    email_input = set_email(driver, bad_email)
    submit(driver, label="invalid_email_missing_domain_after_submit")

    assert has_error_class(email_input), "Invalid email (missing domain) should have 'field-error'."
    out = get_output_text(driver)
    assert "Email:" not in out, "Email line should not be present for invalid email (missing domain)."


def main():
    failures = []
    driver = None
    try:
        driver = make_driver(headless=False)
        for fn in (test_valid_email, test_empty_email, test_invalid_email, test_invalid_email_missing_domain):
            try:
                fn(driver)
                print(f"PASS: {fn.__name__}")
            except AssertionError as e:
                print(f"FAIL: {fn.__name__} -> {e}")
                failures.append((fn.__name__, str(e)))
            except Exception as e:
                print(f"ERROR: {fn.__name__} -> {e}")
                failures.append((fn.__name__, f"Unexpected: {e}"))
    finally:
        if driver is not None:
            driver.quit()

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

