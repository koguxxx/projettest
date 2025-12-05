import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/browser-windows"


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
    options.add_argument("--disable-popup-blocking")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    return drv


def open_page(driver):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tabButton")))


def close_all_children(driver):
    try:
        base = driver.current_window_handle
    except Exception:
        base = None
    try:
        handles = list(driver.window_handles)
    except Exception:
        handles = []
    for h in handles:
        try:
            if base is None or h != base:
                driver.switch_to.window(h)
                driver.close()
        except Exception:
            continue
    if base:
        try:
            driver.switch_to.window(base)
        except Exception:
            pass

def click_and_switch(driver, button_id: str):
    parent = driver.current_window_handle
    before = set(driver.window_handles)
    btn = driver.find_element(By.ID, button_id)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, button_id)))
    btn.click()
    WebDriverWait(driver, 10).until(lambda d: len(set(d.window_handles) - before) == 1)
    new_handle = list(set(driver.window_handles) - before)[0]
    driver.switch_to.window(new_handle)
    # Wait for the new document to be ready
    try:
        WebDriverWait(driver, 8).until(lambda d: d.execute_script("return document.readyState") == "complete")
    except Exception:
        pass
    return new_handle, parent


def current_window_text(driver) -> str:
    # Prefer the Sample page heading, fallback to body text
    try:
        el = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "sampleHeading"))
        )
        return el.text.strip()
    except Exception:
        # Fallback: wait until body has some visible text
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script(
                    "return (document.body && document.body.innerText && document.body.innerText.trim().length) || 0;"
                ) > 0
            )
            return (driver.execute_script("return document.body.innerText") or "").strip()
        except Exception:
            try:
                body = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return (body.text or "").strip()
            except Exception:
                return ""


def quick_body_text(driver, retries: int = 10, delay: float = 0.1) -> str:
    import time as _t
    for _ in range(retries):
        try:
            txt = driver.execute_script("return document && document.body && document.body.innerText || '';")
            txt = (txt or "").strip()
            if txt:
                return txt
        except Exception:
            pass
        _t.sleep(delay)
    return ""


# TC-01: Nouvel onglet avec texte correct
def tc01_new_tab(driver):
    close_all_children(driver)
    open_page(driver)
    _, parent = click_and_switch(driver, "tabButton")
    txt = current_window_text(driver)
    save_screenshot(driver, "browser_tc01_new_tab")
    assert "This is a sample page" in txt, "New tab should show the sample page text."
    driver.close()
    try:
        driver.switch_to.window(parent)
    except Exception:
        pass


# TC-02: Nouvelle fenêtre avec texte correct
def tc02_new_window(driver):
    close_all_children(driver)
    open_page(driver)
    _, parent = click_and_switch(driver, "windowButton")
    txt = current_window_text(driver)
    save_screenshot(driver, "browser_tc02_new_window")
    assert "This is a sample page" in txt, "New window should show the sample page text."
    driver.close()
    try:
        driver.switch_to.window(parent)
    except Exception:
        pass


# TC-03: Petite fenêtre message
# TC-03: Petite fenêtre message
# TC-03: Petite fenêtre message
def tc03_new_window_message(driver):
    close_all_children(driver)
    open_page(driver)
    parent_handle = driver.current_window_handle

    # Cliquer sur le bouton pour ouvrir la fenêtre message
    driver.find_element(By.ID, "messageWindowButton").click()

    import time as _t
    _t.sleep(0.2)  # très court délai pour laisser la fenêtre se créer

    # Récupérer le texte de toutes les fenêtres ouvertes
    child_texts = []
    for handle in driver.window_handles:
        if handle != parent_handle:
            try:
                driver.switch_to.window(handle)
                txt = quick_body_text(driver, retries=10, delay=0.05)
                if txt:
                    child_texts.append(txt.strip())
            except Exception:
                continue

    # Toujours revenir au parent pour capture
    try:
        driver.switch_to.window(parent_handle)
    except Exception:
        pass

    save_screenshot(driver, "browser_tc03_message_window_parent")

    assert len(child_texts) > 0 and any(len(t) > 0 for t in child_texts), \
        "Message window should open and contain some text."

def main():
    failures = []
    tests = [
        ("TC-01 new tab", tc01_new_tab),
        ("TC-02 new window", tc02_new_window),
        ("TC-03 new window message", tc03_new_window_message),
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
                    # Ensure children are closed before quitting
                    close_all_children(driver)
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

