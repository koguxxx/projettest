import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

URL = "https://demoqa.com/buttons"


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
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "doubleClickBtn")))


def get_text_safe(driver, el_id: str) -> str:
    try:
        return driver.find_element(By.ID, el_id).text.strip()
    except Exception:
        return ""


def wait_text(driver, el_id: str, timeout: int = 5) -> str:
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.ID, el_id))
        )
        return el.text.strip()
    except Exception:
        return get_text_safe(driver, el_id)


# TC-01: Double click -> message appears
def tc01_double_click(driver):
    open_page(driver)
    dbl = driver.find_element(By.ID, "doubleClickBtn")
    ActionChains(driver).double_click(dbl).perform()
    msg = wait_text(driver, "doubleClickMessage", timeout=5)
    save_screenshot(driver, "buttons_tc01_double_click")
    assert "You have done a double click" in msg, "Expected double click message."


# TC-02: Right click -> message appears
def tc02_right_click(driver):
    open_page(driver)
    rbtn = driver.find_element(By.ID, "rightClickBtn")
    ActionChains(driver).context_click(rbtn).perform()
    msg = wait_text(driver, "rightClickMessage", timeout=5)
    save_screenshot(driver, "buttons_tc02_right_click")
    assert "You have done a right click" in msg, "Expected right click message."


# TC-03: Dynamic click (simple left click on "Click Me") -> message appears
def tc03_dynamic_click(driver):
    open_page(driver)
    dyn = driver.find_element(By.XPATH, "//button[text()='Click Me']")
    dyn.click()
    msg = wait_text(driver, "dynamicClickMessage", timeout=5)
    save_screenshot(driver, "buttons_tc03_dynamic_click")
    assert "You have done a dynamic click" in msg, "Expected dynamic click message."


# TC-04: Accessibilité (3 boutons visibles et interactifs)
def tc04_accessibility(driver):
    open_page(driver)
    dbl = driver.find_element(By.ID, "doubleClickBtn")
    rbtn = driver.find_element(By.ID, "rightClickBtn")
    dyn = driver.find_element(By.XPATH, "//button[text()='Click Me']")
    save_screenshot(driver, "buttons_tc04_accessibility")
    for el in (dbl, rbtn, dyn):
        assert el.is_displayed() and el.is_enabled(), "Buttons should be visible and enabled."


# TC-05: Left click on right click button -> no message
def tc05_left_click_on_right_button_no_message(driver):
    open_page(driver)
    rbtn = driver.find_element(By.ID, "rightClickBtn")
    rbtn.click()
    save_screenshot(driver, "buttons_tc05_left_click_right_button")
    # Right click message should NOT appear on left click
    msg = get_text_safe(driver, "rightClickMessage")
    assert not msg, "Right click message should not appear on left click."


def main():
    failures = []
    tests = [
        ("TC-01 double click", tc01_double_click),
        ("TC-02 right click", tc02_right_click),
        ("TC-03 dynamic click", tc03_dynamic_click),
        ("TC-04 accessibility", tc04_accessibility),
        ("TC-05 left click on right click button", tc05_left_click_on_right_button_no_message),
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

