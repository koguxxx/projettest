import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://demoqa.com/upload-download"


def downloads_dir() -> str:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    path = os.path.join(desktop, "DemoQA_Downloads")
    os.makedirs(path, exist_ok=True)
    return path


def make_driver(headless: bool = False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "download.default_directory": downloads_dir(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    return drv


def open_page(driver):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "uploadFile")))


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


def create_temp_file() -> str:
    dir_path = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(dir_path, exist_ok=True)
    filename = f"demoqa_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(dir_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("Hello DemoQA Upload Test\n")
    return path


def list_files(path: str) -> set[str]:
    try:
        return set(os.listdir(path))
    except Exception:
        return set()


def wait_for_new_download(prev: set[str], folder: str, timeout: int = 20) -> str | None:
    end = time.time() + timeout
    while time.time() < end:
        curr = list_files(folder)
        new = [f for f in curr - prev if not f.endswith('.crdownload')]
        if new:
            file_path = os.path.join(folder, new[0])
            # Ensure file write complete
            if not file_path.endswith('.crdownload') and os.path.exists(file_path):
                return file_path
        time.sleep(0.3)
    return None


def test_upload_shows_filename(driver):
    open_page(driver)
    file_path = create_temp_file()
    upload = driver.find_element(By.ID, "uploadFile")
    upload.send_keys(file_path)
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "uploadedFilePath")))
    text = driver.find_element(By.ID, "uploadedFilePath").text
    input_value = upload.get_attribute("value") or ""
    save_screenshot(driver, "upload_after_select")
    filename = os.path.basename(file_path)
    # DemoQA shows a browser-provided fake path (C:\\fakepath\\<filename>)
    assert filename in text, "Uploaded file name should appear in the result text."
    assert filename in input_value, "Input value should include the uploaded file name."
    assert "fakepath" in input_value.lower() or "fakepath" in text.lower(), "Browser should expose a fake path for security."


def test_download_saves_file(driver):
    open_page(driver)
    folder = downloads_dir()
    before = list_files(folder)
    btn = driver.find_element(By.ID, "downloadButton")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "downloadButton")))
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
    path = wait_for_new_download(before, folder, timeout=25)
    save_screenshot(driver, "download_after_click")
    assert path is not None and os.path.isfile(path), "A file should be downloaded into the configured folder."


def main():
    failures = []
    driver = None
    try:
        driver = make_driver(headless=False)
        for fn in (test_upload_shows_filename, test_download_saves_file):
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

