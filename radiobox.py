import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/radio-button"


def make_driver(headless: bool = False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Selenium Manager (Selenium >=4.6) resolves chromedriver automatically
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    return drv


def open_page(driver):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "custom-control")))


def scroll_into_view(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)


def label_for(driver, input_id: str):
    # Labels have css selector label[for="id"]
    return driver.find_element(By.CSS_SELECTOR, f'label[for="{input_id}"]')


def input_by_id(driver, input_id: str):
    return driver.find_element(By.ID, input_id)


def click_option(driver, input_id: str, screenshot_label: str | None = None):
    lbl = label_for(driver, input_id)
    scroll_into_view(driver, lbl)
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'label[for="{input_id}"]')))
    try:
        lbl.click()
    except Exception:
        driver.execute_script("arguments[0].click();", lbl)
    # Wait until selection state updates
    WebDriverWait(driver, 5).until(lambda d: input_by_id(d, input_id).is_selected() or not input_by_id(d, input_id).is_enabled())
    if screenshot_label:
        save_screenshot(driver, screenshot_label)


def get_result_text(driver) -> str:
    try:
        el = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "text-success")))
        return el.text.strip()
    except Exception:
        return ""


def is_selected(driver, input_id: str) -> bool:
    return input_by_id(driver, input_id).is_selected()


def is_enabled(driver, input_id: str) -> bool:
    return input_by_id(driver, input_id).is_enabled()


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


def test_yes_selection_exclusive(driver):
    open_page(driver)
    click_option(driver, "yesRadio", screenshot_label="radio_yes_after_click")

    assert is_selected(driver, "yesRadio"), "Yes should be selected after clicking."
    assert not is_selected(driver, "impressiveRadio"), "Impressive should NOT be selected when Yes is selected."
    assert get_result_text(driver) == "Yes", "Result text should show 'Yes'."


def test_impressive_selection_exclusive(driver):
    open_page(driver)
    click_option(driver, "impressiveRadio", screenshot_label="radio_impressive_after_click")

    assert is_selected(driver, "impressiveRadio"), "Impressive should be selected after clicking."
    assert not is_selected(driver, "yesRadio"), "Yes should NOT be selected when Impressive is selected."
    assert get_result_text(driver) == "Impressive", "Result text should show 'Impressive'."


def test_no_is_disabled(driver):
    open_page(driver)
    no_input = input_by_id(driver, "noRadio")
    assert not no_input.is_enabled(), "'No' option should be disabled."


def main():
    failures = []
    driver = None
    try:
        driver = make_driver(headless=False)
        for fn in (test_yes_selection_exclusive, test_impressive_selection_exclusive, test_no_is_disabled):
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

