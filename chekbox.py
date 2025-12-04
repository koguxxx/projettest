from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Constantes du Test
URL = "https://demoqa.com/checkbox"
# XPath générique pour localiser l'icône de la CheckBox
XPATH_CHECKBOX_BY_NAME = "//label[text()='{}']/span[@class='rct-checkbox']"
# LOCATOR AJOUTÉ : Pour le bouton "Expand All"
XPATH_EXPAND_ALL_BUTTON = "//button[@title='Expand all']" 
# ID de l'élément qui affiche le résultat (ID_RESULT)
ID_RESULT = "result" 
# NOUVELLE CONSTANTE : XPath pour l'élément 'Home'
XPATH_HOME_LABEL = "//label[text()='Home']"

# Crée un dossier pour les captures d'écran en cas d'échec inattendu
if not os.path.exists("preuves_automatisation_checkbox"):
    os.makedirs("preuves_automatisation_checkbox")

def expand_all_tree(driver):
    """Clique sur le bouton 'Expand All' pour s'assurer que tous les éléments sont dans le DOM."""
    try:
        expand_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, XPATH_EXPAND_ALL_BUTTON))
        )
        expand_button.click()
        print("Arborescence entièrement déployée (Expand All cliqué).")
        time.sleep(1) 
    except Exception:
        # Tente de cliquer sur l'icône de réduction du Home (si le bouton Expand All est absent)
        try:
             driver.find_element(By.CLASS_NAME, "rct-collapse-btn").click()
        except NoSuchElementException:
             pass 

def setup_driver():
    """Initialise, ouvre le navigateur ET DÉPLOIE L'ARBORESCENCE."""
    driver = webdriver.Chrome()
    driver.get(URL)
    driver.maximize_window()
    
    # 🌟 CORRECTION CLÉ : Attendre l'élément 'Home' (statique) au lieu de 'ID_RESULT' (dynamique)
    print("Attente de l'élément principal 'Home'...")
    WebDriverWait(driver, 20).until( 
        EC.presence_of_element_located((By.XPATH, XPATH_HOME_LABEL))
    )
    
    expand_all_tree(driver) 
    return driver

def save_screenshot(driver, test_id, description):
    """Prend une capture d'écran avec un nom de fichier horodaté et descriptif."""
    filename = f"preuves_automatisation_checkbox/{test_id}_ECHEC_{description}_{int(time.time())}.png"
    driver.save_screenshot(filename)
    return filename

def click_checkbox(driver, name):
    """Clique sur la case à cocher associée à un nom de texte donné."""
    checkbox_xpath = XPATH_CHECKBOX_BY_NAME.format(name)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, checkbox_xpath))
    )
    driver.find_element(By.XPATH, checkbox_xpath).click()
    time.sleep(0.5) 
    
def get_result_text(driver):
    """Récupère le texte complet de la zone de résultat."""
    try:
        # L'élément ID_RESULT est créé seulement après la première interaction.
        return driver.find_element(By.ID, ID_RESULT).text.replace("You have selected :", "").strip()
    except NoSuchElementException:
        return ""

# (Le reste du code des tests est inchangé)
# ... (test_tc_cb_03_cascade_positive, test_tc_cb_05_etat_partiel, test_tc_cb_06_affichage_resultat, et le bloc if __name__ main) ...
def save_screenshot(driver, test_id, description):
    """Prend une capture d'écran avec un nom de fichier horodaté et descriptif."""
    filename = f"preuves_automatisation_checkbox/{test_id}_ECHEC_{description}_{int(time.time())}.png"
    driver.save_screenshot(filename)
    return filename

def click_checkbox(driver, name):
    """Clique sur la case à cocher associée à un nom de texte donné."""
    checkbox_xpath = XPATH_CHECKBOX_BY_NAME.format(name)
    # Utilisation d'une attente pour s'assurer que l'élément est cliquable APRÈS l'expansion
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, checkbox_xpath))
    )
    driver.find_element(By.XPATH, checkbox_xpath).click()
    time.sleep(0.5) # Petite attente pour que l'état se mette à jour
    
def get_result_text(driver):
    """Récupère le texte complet de la zone de résultat."""
    try:
        return driver.find_element(By.ID, ID_RESULT).text.replace("You have selected :", "").strip()
    except NoSuchElementException:
        return ""
# ... (La fonction test_tc_cb_03_cascade_positive, test_tc_cb_05_etat_partiel, et test_tc_cb_06_affichage_resultat sont inchangées ici) ...
def is_parent_partial(driver, parent_name):
    """Vérifie si le parent est en état Partiel (présence de la classe 'rct-icon-half-check')."""
    xpath_parent = XPATH_CHECKBOX_BY_NAME.format(parent_name) + "/svg"
    try:
        # Vérifie si l'icône de l'état partiel est présente dans l'icône CheckBox du parent
        parent_element = driver.find_element(By.XPATH, xpath_parent)
        # La classe CSS 'rct-icon-half-check' indique l'état partiel (le tiret '-')
        return "rct-icon-half-check" in parent_element.get_attribute("class")
    except NoSuchElementException:
        return False

def test_tc_cb_03_cascade_positive():
    """Vérifie que cocher 'Home' coche TOUS les éléments (17 au total)."""
    test_id = "TC-CB-03"
    driver = setup_driver()
    try:
        # 1. Étapes : Cocher Home (Maintenant l'élément est trouvé car l'arbre est déployé)
        click_checkbox(driver, "Home")
        
        # 2. ASSERTION : Le message de résultat doit contenir tous les éléments attendus.
        expected_items = ["desktop", "notes", "commands", "documents", "workspace", "react", "angular", "veu", 
                          "office", "public", "private", "classified", "general", "downloads", "wordFile", "excelFile"]
        
        result_text = get_result_text(driver)
        
        # Vérifier si TOUS les mots clés attendus sont dans le résultat affiché
        for item in expected_items:
            assert item.lower() in result_text.lower(), f"L'élément '{item}' n'a pas été trouvé dans le résultat après la cascade."

        print(f"[{test_id} PASSÉ] : La cascade positive a réussi. Tous les éléments sont cochés.")
        
    except AssertionError as e:
        capture = save_screenshot(driver, test_id, "Cascade_Echouee")
        print(f"[{test_id} ÉCHOUÉ] : {e} Preuve : {capture}")
        
    finally:
        driver.quit()

def test_tc_cb_05_etat_partiel():
    """Vérifie que le parent Documents passe à l'état Partiel après la désélection d'un enfant."""
    test_id = "TC-CB-05"
    driver = setup_driver()
    try:
        # 1. Étapes : Cocher le Parent 'Documents' (sélectionne tous ses enfants)
        click_checkbox(driver, "Documents")

        # 2. Étapes : Décocher un seul enfant
        click_checkbox(driver, "WorkSpace")
        
        # 3. ASSERTION : Le parent 'Documents' doit être en état Partiel
        if is_parent_partial(driver, "Documents"):
            print(f"[{test_id} PASSÉ] : Le parent 'Documents' a correctement affiché l'état Partiel.")
        else:
            capture = save_screenshot(driver, test_id, "Etat_Partiel_Echoue")
            raise AssertionError(f"[{test_id} ÉCHOUÉ] : Le parent 'Documents' n'est pas passé à l'état Partiel. Preuve : {capture}")

    except AssertionError as e:
        print(e)
    except Exception as e:
        print(f"[{test_id} ERREUR TECHNIQUE] : {e}")
    finally:
        driver.quit()

def test_tc_cb_06_affichage_resultat():
    """Vérifie que l'affichage de résultat correspond exactement aux sélections."""
    test_id = "TC-CB-06"
    driver = setup_driver()
    try:
        # 1. Étapes : Sélectionner des éléments non liés
        click_checkbox(driver, "Desktop")
        click_checkbox(driver, "General")
        
        # 2. ASSERTION : Le texte doit correspondre exactement, sans erreur de format.
        expected_result = "desktop, general"
        actual_result = get_result_text(driver)
        
        # L'assertion vérifie la correspondance exacte
        assert actual_result == expected_result, f"Résultat incorrect. Attendu : '{expected_result}', Obtenu : '{actual_result}'"

        print(f"[{test_id} PASSÉ] : L'affichage du résultat est exact et correctement formaté.")
        
    except AssertionError as e:
        capture = save_screenshot(driver, test_id, "Resultat_Format_Echoue")
        print(f"[{test_id} ÉCHOUÉ] : {e} Preuve : {capture}")
        
    finally:
        driver.quit()
if __name__ == "__main__":
    print("--- DÉMARRAGE DE L'AUTOMATISATION CHECKBOX (Phase 4) ---")
    
    # Exécution des tests
    test_tc_cb_03_cascade_positive()
    test_tc_cb_05_etat_partiel()
    test_tc_cb_06_affichage_resultat()

    print("\n--- SUITE DE TESTS CHECKBOX TERMINÉE ---")
    print("Vérifiez les résultats dans la console et les captures d'écran dans le dossier 'preuves_automatisation_checkbox'.")