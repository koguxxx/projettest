import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/tabs"


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
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "demo-tab-what")))


def click_tab(driver, tab_id: str):
    el = driver.find_element(By.ID, tab_id)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, tab_id)))
    try:
        el.click()
    except Exception:
        # Fallback to JS click if intercepted by nav container
        driver.execute_script("arguments[0].click();", el)


def tab_active(driver, tab_id: str) -> bool:
    try:
        el = driver.find_element(By.ID, tab_id)
        cls = (el.get_attribute("class") or "").lower()
        return "active" in cls and "disabled" not in cls
    except Exception:
        return False


def content_visible(driver, panel_id: str) -> bool:
    try:
        el = driver.find_element(By.ID, panel_id)
        cls = (el.get_attribute("class") or "").lower()
        return "active" in cls and el.is_displayed()
    except Exception:
        return False


def panel_text(driver, panel_id: str) -> str:
    try:
        return driver.find_element(By.ID, panel_id).text.strip()
    except Exception:
        return ""


# TC-01: Affichage initial -> What actif
def tc01_initial_state(driver):
    open_page(driver)
    save_screenshot(driver, "tabs_tc01_initial_state")
    assert tab_active(driver, "demo-tab-what") and content_visible(driver, "demo-tabpane-what"), "'What' tab should be active with content visible."


# TC-02: Onglet What
def tc02_tab_what(driver):
    open_page(driver)
    click_tab(driver, "demo-tab-what")
    WebDriverWait(driver, 5).until(lambda d: tab_active(d, "demo-tab-what") and content_visible(d, "demo-tabpane-what"))
    save_screenshot(driver, "tabs_tc02_what")
    assert panel_text(driver, "demo-tabpane-what"), "What content should be visible and non-empty."


# TC-03: Onglet Origin
def tc03_tab_origin(driver):
    open_page(driver)
    click_tab(driver, "demo-tab-origin")
    WebDriverWait(driver, 5).until(lambda d: tab_active(d, "demo-tab-origin") and content_visible(d, "demo-tabpane-origin"))
    save_screenshot(driver, "tabs_tc03_origin")
    assert panel_text(driver, "demo-tabpane-origin"), "Origin content should be visible."


# TC-04: Onglet Use
def tc04_tab_use(driver):
    open_page(driver)
    click_tab(driver, "demo-tab-use")
    WebDriverWait(driver, 5).until(lambda d: tab_active(d, "demo-tab-use") and content_visible(d, "demo-tabpane-use"))
    save_screenshot(driver, "tabs_tc04_use")
    assert panel_text(driver, "demo-tabpane-use"), "Use content should be visible."


# TC-05: Onglet More
def tc05_tab_more(driver):
    open_page(driver)
    click_tab(driver, "demo-tab-more")
    WebDriverWait(driver, 5).until(lambda d: tab_active(d, "demo-tab-more") and content_visible(d, "demo-tabpane-more"))
    save_screenshot(driver, "tabs_tc05_more")
    assert panel_text(driver, "demo-tabpane-more"), "More content should be visible."


# TC-06: Lisibilité du texte (chaque onglet)
def tc06_readability(driver):
    open_page(driver)
    for tab_id, pane_id in (
        ("demo-tab-what", "demo-tabpane-what"),
        ("demo-tab-origin", "demo-tabpane-origin"),
        ("demo-tab-use", "demo-tabpane-use"),
        ("demo-tab-more", "demo-tabpane-more"),
    ):
        click_tab(driver, tab_id)
        WebDriverWait(driver, 5).until(lambda d, t=tab_id, p=pane_id: tab_active(d, t) and content_visible(d, p))
        txt = panel_text(driver, pane_id)
        assert txt and len(txt) > 20, f"Content for {pane_id} should be readable and non-trivial."
    save_screenshot(driver, "tabs_tc06_readability")


# TC-07: Clics multiples (stabilité)
def tc07_multiple_clicks(driver):
    open_page(driver)
    order = [
        ("demo-tab-origin", "demo-tabpane-origin"),
        ("demo-tab-use", "demo-tabpane-use"),
        ("demo-tab-what", "demo-tabpane-what"),
        ("demo-tab-more", "demo-tabpane-more"),
    ]
    for _ in range(3):
        for tab_id, pane_id in order:
            click_tab(driver, tab_id)
            WebDriverWait(driver, 5).until(lambda d, t=tab_id, p=pane_id: tab_active(d, t) and content_visible(d, p))
            txt = panel_text(driver, pane_id)
            assert txt, f"After multiple clicks, content for {pane_id} should remain visible."
    save_screenshot(driver, "tabs_tc07_multiple_clicks")


def main():
    failures = []
    tests = [
        ("TC-01 initial state", tc01_initial_state),
        ("TC-02 tab what", tc02_tab_what),
        ("TC-03 tab origin", tc03_tab_origin),
        ("TC-04 tab use", tc04_tab_use),
        ("TC-05 tab more", tc05_tab_more),
        ("TC-06 readability", tc06_readability),
        ("TC-07 multiple clicks", tc07_multiple_clicks),
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

