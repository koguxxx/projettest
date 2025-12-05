import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/accordian"


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
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "section1Heading")))


def is_visible(driver, locator) -> bool:
    try:
        el = driver.find_element(*locator)
        return el.is_displayed() and el.size.get("height", 0) > 0 and (el.text or "").strip() != ""
    except Exception:
        return False


def heading_expanded(driver, heading_id: str) -> bool:
    try:
        el = driver.find_element(By.ID, heading_id)
        expanded = (el.get_attribute("aria-expanded") or "").lower()
        if expanded == "":
            # Try descendant that actually carries the aria-expanded attribute
            try:
                el2 = el.find_element(By.CSS_SELECTOR, "*[aria-expanded]")
                expanded = (el2.get_attribute("aria-expanded") or "").lower()
            except Exception:
                expanded = ""
        return expanded == "true"
    except Exception:
        return False


def content_shown(driver, content_id: str) -> bool:
    try:
        el = driver.find_element(By.ID, content_id)
        cls = (el.get_attribute("class") or "").lower()
        # Bootstrap-like 'show' indicates visible; also check height
        if "show" in cls:
            return True
        # fallback to rendered height
        h = el.size.get("height", 0)
        return el.is_displayed() and h > 0
    except Exception:
        return False


def click_heading(driver, heading_id: str):
    hdr = driver.find_element(By.ID, heading_id)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hdr)
    try:
        WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.ID, heading_id)))
        hdr.click()
    except Exception:
        # Fallback to clicking a clickable child or JS click
        try:
            btn = hdr.find_element(By.CSS_SELECTOR, "button, [role='button'], *")
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            driver.execute_script("arguments[0].click();", hdr)


def get_section_text(driver, content_id: str) -> str:
    try:
        el = driver.find_element(By.ID, content_id)
        return el.text.strip()
    except Exception:
        return ""


# TC-01: Ouverture de la première section
def tc01_open_first(driver):
    open_page(driver)
    click_heading(driver, "section1Heading")
    WebDriverWait(driver, 10).until(lambda d: content_shown(d, "section1Content"))
    save_screenshot(driver, "accordion_tc01_open_first")
    txt = get_section_text(driver, "section1Content")
    assert txt, "First section text should appear."


# TC-02: Fermeture de la première section
def tc02_close_first(driver):
    open_page(driver)
    # Open then close
    click_heading(driver, "section1Heading")
    WebDriverWait(driver, 10).until(lambda d: content_shown(d, "section1Content"))
    # On this page, sections behave like an accordion: opening another section collapses the first
    click_heading(driver, "section2Heading")
    save_screenshot(driver, "accordion_tc02_close_first")
    WebDriverWait(driver, 10).until(lambda d: (not content_shown(d, "section1Content")))
    assert not content_shown(driver, "section1Content"), "First section content should be hidden after closing."


# TC-03: Ouverture de la deuxième section
def tc03_open_second(driver):
    open_page(driver)
    click_heading(driver, "section2Heading")
    WebDriverWait(driver, 10).until(lambda d: content_shown(d, "section2Content"))
    save_screenshot(driver, "accordion_tc03_open_second")
    assert get_section_text(driver, "section2Content"), "Second section text should be visible."


# TC-04: Ouverture de la troisième section
def tc04_open_third(driver):
    open_page(driver)
    click_heading(driver, "section3Heading")
    WebDriverWait(driver, 10).until(lambda d: content_shown(d, "section3Content"))
    save_screenshot(driver, "accordion_tc04_open_third")
    assert get_section_text(driver, "section3Content"), "Third section text should be visible and readable."


# TC-05: Ouverture multiple (plusieurs sections ouvertes simultanément)
def tc05_multiple_open(driver):
    open_page(driver)
    # Open 1 and 2
    click_heading(driver, "section1Heading")
    WebDriverWait(driver, 10).until(lambda d: content_shown(d, "section1Content"))
    click_heading(driver, "section2Heading")
    WebDriverWait(driver, 10).until(lambda d: content_shown(d, "section2Content"))
    save_screenshot(driver, "accordion_tc05_multiple_open")
    # DemoQA uses an accordion where only one section stays open; ensure exclusivity
    assert (not content_shown(driver, "section1Content")) and content_shown(driver, "section2Content"), "Opening section 2 should close section 1."


# TC-06: Vérification du texte dans chaque section
def tc06_text_in_each(driver):
    open_page(driver)
    for hid, cid in (
        ("section1Heading", "section1Content"),
        ("section2Heading", "section2Content"),
        ("section3Heading", "section3Content"),
    ):
        click_heading(driver, hid)
        WebDriverWait(driver, 5).until(lambda d, c=cid: is_visible(d, (By.ID, c)))
        txt = get_section_text(driver, cid)
        assert txt and len(txt) > 20, f"Section {cid} should show a reasonable amount of text."
    save_screenshot(driver, "accordion_tc06_text_each")


def main():
    failures = []
    tests = [
        ("TC-01 open first", tc01_open_first),
        ("TC-02 close first", tc02_close_first),
        ("TC-03 open second", tc03_open_second),
        ("TC-04 open third", tc04_open_third),
        ("TC-05 multiple open", tc05_multiple_open),
        ("TC-06 text in each", tc06_text_in_each),
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

