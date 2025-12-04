import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/login"
VALID_USERNAME = "koguxx"
VALID_PASSWORD = "123456789aZ*"


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


def open_login(driver):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login")))


def set_input(driver, id_, value: str):
    el = driver.find_element(By.ID, id_)
    el.clear()
    el.send_keys(value)
    return el


def click_login(driver):
    btn = driver.find_element(By.ID, "login")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "login")))
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)


def on_profile(driver, timeout: int = 10) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.url_contains("/profile"),
                EC.visibility_of_element_located((By.ID, "userName-value"))
            )
        )
        return True
    except Exception:
        return False


def get_error_message(driver) -> str:
    # DemoQA uses #name for auth errors
    try:
        return driver.find_element(By.ID, "name").text.strip()
    except Exception:
        return ""


def wait_error_message(driver, timeout: int = 5) -> str:
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.ID, "name"))
        )
        return el.text.strip()
    except Exception:
        return get_error_message(driver)


# TC-01: Connexion valide
def tc01_valid_login(driver):
    open_login(driver)
    set_input(driver, "userName", VALID_USERNAME)
    set_input(driver, "password", VALID_PASSWORD)
    click_login(driver)
    ok = on_profile(driver, timeout=10)
    save_screenshot(driver, "login_tc01_after_login")
    assert ok, "Expected redirect to profile (or username shown) for valid login."


# TC-02: Mot de passe incorrect
def tc02_wrong_password(driver):
    open_login(driver)
    set_input(driver, "userName", VALID_USERNAME)
    set_input(driver, "password", "WrongPassword!1")
    click_login(driver)
    save_screenshot(driver, "login_tc02_wrong_password")
    err = wait_error_message(driver, timeout=5)
    assert "invalid username or password" in err.lower(), "Expected 'Invalid username or password!' message."
    assert not on_profile(driver, timeout=3), "Should not navigate to profile for wrong password."


# TC-03: Username incorrect
def tc03_wrong_username(driver):
    open_login(driver)
    set_input(driver, "userName", "userFake")
    set_input(driver, "password", VALID_PASSWORD)
    click_login(driver)
    save_screenshot(driver, "login_tc03_wrong_username")
    err = wait_error_message(driver, timeout=5)
    assert err, "Expected an error message for wrong username."
    assert not on_profile(driver, timeout=3), "Should not navigate to profile with wrong username."


# TC-04: Champs vides
def tc04_empty_fields(driver):
    open_login(driver)
    click_login(driver)
    save_screenshot(driver, "login_tc04_empty_fields")
    # Expect to remain on login page and not reach profile
    assert driver.current_url.endswith("/login"), "Should stay on login page when fields are empty."
    assert not on_profile(driver, timeout=3)


# TC-05: Mot de passe vide
def tc05_password_empty(driver):
    open_login(driver)
    set_input(driver, "userName", VALID_USERNAME)
    set_input(driver, "password", "")
    click_login(driver)
    save_screenshot(driver, "login_tc05_password_empty")
    # Expect an error and no profile navigation
    err = wait_error_message(driver, timeout=5)
    assert err or driver.current_url.endswith("/login"), "Expected an error or to remain on login page."
    assert not on_profile(driver, timeout=3), "Should not navigate to profile when password is empty."


def main():
    failures = []
    tests = [
        ("TC-01 valid login", tc01_valid_login),
        ("TC-02 wrong password", tc02_wrong_password),
        ("TC-03 wrong username", tc03_wrong_username),
        ("TC-04 empty fields", tc04_empty_fields),
        ("TC-05 password empty", tc05_password_empty),
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

