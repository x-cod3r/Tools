from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
import time
import os
import random
from dotenv import load_dotenv

load_dotenv()
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_PROFILE_NAME = os.getenv("TWITTER_PROFILE_NAME")
TWITTER_VERIFICATION_INPUT = os.getenv("TWITTER_VERIFICATION_INPUT", TWITTER_USERNAME)

MAX_DELETES_PER_SESSION = 15
MAX_SCROLL_ATTEMPTS_WITHOUT_DELETE = 7 # Slightly increased as we debug
MAX_TOTAL_ITERATIONS = 70
DELAY_BETWEEN_ACTIONS_MIN = 2.8 # Slightly increased
DELAY_BETWEEN_ACTIONS_MAX = 4.8 # Slightly increased
DELAY_AFTER_SCROLL_MIN = 3.5
DELAY_AFTER_SCROLL_MAX = 5.0
DELAY_AFTER_SUCCESSFUL_DELETE = 4.0 # Specific delay after a delete

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # options.add_argument("--headless") # Optional: for running without a visible browser window
    # options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Optional
    driver = webdriver.Chrome(options=options)
    return driver

def login_to_twitter(driver, username, password, verification_input):
    print("Attempting to log in to Twitter/X...")
    driver.get("https://twitter.com/login")
    try:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(username)
        next_button_xpath = "//button[.//span[contains(text(),'Next')]]"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, next_button_xpath))).click()
        print("Username entered, clicked Next.")
        time.sleep(random.uniform(1.5, 2.5))

        try:
            verification_prompt_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"))
            )
            print("Suspicious activity prompt detected. Entering verification input.")
            verification_prompt_input.send_keys(verification_input)
            verification_next_button_xpath = "//button[@data-testid='ocfEnterTextNextButton']"
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, verification_next_button_xpath))).click()
            print("Verification input submitted, clicked Next.")
            time.sleep(random.uniform(1.5, 2.5))
        except TimeoutException:
            print("No suspicious activity prompt detected, or it timed out. Proceeding to password.")
            pass

        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)
        login_button_xpath = "//button[@data-testid='LoginForm_Login_Button']"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, login_button_xpath))).click()
        print("Password entered, clicked Log in.")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-testid='AppTabBar_Home_Link']"))
        )
        print("Successfully logged in.")
        return True
    except TimeoutException as e:
        print(f"Timeout during login: {e}. Current URL: {driver.current_url}")
        driver.save_screenshot("login_timeout_error.png")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}. Current URL: {driver.current_url}")
        driver.save_screenshot("login_generic_error.png")
        return False

def navigate_to_profile_with_replies(driver, profile_name):
    if not profile_name:
        print("Twitter profile name not set in .env. Cannot navigate.")
        return False
    profile_name_cleaned = profile_name.lstrip('@')
    replies_url = f"https://x.com/{profile_name_cleaned}/with_replies"
    print(f"Navigating to profile page with replies: {replies_url}")
    driver.get(replies_url)
    try:
        WebDriverWait(driver, 25).until( # Increased wait time
            EC.any_of(
                 EC.presence_of_element_located((By.XPATH, "//article[@data-testid='tweet']")),
                 EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'hasn’t Tweeted yet')]")),
                 EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'When they do, their Tweets will show up here')]")),
                 EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'No Posts yet')]")) # New X variation
            )
        )
        print("Profile page with replies loaded (or no content message shown).")
        return True
    except TimeoutException:
        print("Timeout waiting for profile page (with replies) elements. Page might be empty or structure changed significantly.")
        driver.save_screenshot("navigate_to_with_replies_timeout.png")
        return True
    except Exception as e:
        print(f"Error navigating to profile page with replies: {e}")
        driver.save_screenshot("navigate_to_with_replies_error.png")
        return False

def scroll_down(driver):
    print("Scrolling down...")
    driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);") # Scroll by 80% of viewport height
    time.sleep(random.uniform(DELAY_AFTER_SCROLL_MIN, DELAY_AFTER_SCROLL_MAX))

def attempt_single_reply_delete(driver):
    print("==> Inside attempt_single_reply_delete function...")
    try:
        article_xpath = "//article[@data-testid='tweet']"
        try:
            WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.XPATH, article_xpath)))
        except TimeoutException:
            print(f"  [INFO] No articles found with XPath: {article_xpath} after waiting. Current URL: {driver.current_url}")
            return False
            
        articles = driver.find_elements(By.XPATH, article_xpath)
        
        if not articles:
            print(f"  [INFO] No articles found (after initial presence check). Current URL: {driver.current_url}")
            return False
        
        print(f"  [INFO] Found {len(articles)} articles to check in current view.")

        for i, article_element in enumerate(articles): # Loop over articles
            print(f"\n  [ARTICLE {i+1}/{len(articles)}] Processing...")
            # THIS IS THE TRY BLOCK THAT NEEDS CORRECTLY INDENTED EXCEPTS
            try: 
                try: # Inner try for getting text snippet, less critical
                    article_text_snippet = " ".join(article_element.text.split()[:10])
                    print(f"    Targeting article snippet: '{article_text_snippet}...'")
                except StaleElementReferenceException:
                    print("    [WARN] Article became stale before getting text snippet. Skipping for text.")
                except Exception as e_text:
                    print(f"    [WARN] Could not get article text snippet: {e_text}. Proceeding.")

                # Ensure article_element is still valid before scrolling
                if not article_element.is_displayed(): # Basic check
                     print("    [WARN] Article element no longer displayed before scroll. Skipping article.")
                     continue


                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'nearest'});", 
                    article_element
                )
                time.sleep(1.8) 

                # 1. Click the 'more options' (three dots) button
                # ... (rest of the "more options" finding logic as before) ...
                svg_path_d_attribute = "M3 12c0-1.1.9-2 2-2s2 .9 2 2-.9 2-2 2-2-.9-2-2zm9 2c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm7 0c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"
                more_options_button_xpaths_to_try = [
                    ".//div[@data-testid='caret']", ".//div[@aria-label='More']", ".//button[@aria-label='More']",
                    ".//div[contains(@aria-label, 'More Tweet actions')]", ".//div[contains(@aria-label, 'More options')]",
                    f".//div[.//svg[.//path[@d='{svg_path_d_attribute}']]]",
                    f".//div[@role='button' and .//svg[.//path[@d='{svg_path_d_attribute}']]]",
                    f".//div[.//svg[@aria-label='More']]", f".//button[.//svg[.//path[@d='{svg_path_d_attribute}']]]"
                ]
                more_options_button = None
                
                print(f"    1. Attempting to find 'more options' button for article {i+1}...")
                for xpath_idx, xpath_attempt in enumerate(more_options_button_xpaths_to_try):
                    try:
                        candidate_button = WebDriverWait(article_element, 2).until(
                            EC.presence_of_element_located((By.XPATH, xpath_attempt))
                        )
                        if candidate_button.is_displayed() and candidate_button.is_enabled():
                            more_options_button = WebDriverWait(article_element, 1).until(
                                EC.element_to_be_clickable((By.XPATH, xpath_attempt))
                            )
                            print(f"      SUCCESS: 'More options' button found and clickable with XPath: {xpath_attempt}")
                            break 
                    except: pass 

                if not more_options_button:
                    print(f"    [ERROR] Could not find a clickable 'more options' button for article {i+1}.")
                    continue 

                print("    'More options' button identified. Attempting to click...")
                more_options_button.click()
                print("    Clicked 'more options' menu.")
                time.sleep(random.uniform(1.5, 2.2))

                # 2. Click the 'Delete' option from the dropdown menu
                # ... (rest of the "Delete" option finding logic as before) ...
                delete_option_xpaths_to_try = [
                    "//div[@role='menuitem'][.//span[text()='Delete']]", "//div[@role='menuitem'][.//span[contains(text(),'Delete')]]",
                    "//div[@role='menuitem'][.//div[contains(text(),'Delete')]]", "//div[@role='menuitem'][contains(@aria-label,'Delete')]",
                    "//div[@role='menuitem' and ./span[text()='Delete']]", "//div[@role='menuitem' and ./span[contains(text(),'Delete')]]"
                ]
                delete_option_found = False
                delete_option_element = None

                print(f"    2. Attempting to find 'Delete' option in menu...")
                for idx, del_xpath in enumerate(delete_option_xpaths_to_try):
                    try:
                        delete_option_candidate = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, del_xpath))
                        )
                        if delete_option_candidate.is_displayed():
                            delete_option_element = delete_option_candidate
                            print(f"      SUCCESS: 'Delete' option found and clickable with XPath: {del_xpath}")
                            delete_option_found = True
                            break
                    except: pass

                if not delete_option_found or not delete_option_element:
                    print(f"    [ERROR] Could not find 'Delete' option in menu for article {i+1}.")
                    driver.save_screenshot(f"debug_DELETE_OPTION_NOT_FOUND_article_{i+1}.png")
                    try:
                        driver.find_element(By.XPATH, "//body").send_keys(Keys.ESCAPE)
                        time.sleep(0.7)
                    except Exception as esc_err: print(f"    [WARN] Could not send ESCAPE key: {esc_err}")
                    continue 

                print("    'Delete' option found. Attempting to click...")
                delete_option_element.click()
                print(f"  [SUCCESS] Clicked 'Delete' for article {i+1}. Assuming direct delete.")
                time.sleep(random.uniform(DELAY_AFTER_SUCCESSFUL_DELETE - 1.0, DELAY_AFTER_SUCCESSFUL_DELETE + 1.0))
                return True 

            # THESE EXCEPT BLOCKS MUST BE ALIGNED WITH THE 'try' AT THE START OF ARTICLE PROCESSING
            except StaleElementReferenceException:
                print(f"    [WARN] Stale element reference during processing article {i+1}. DOM likely changed. Assuming delete was successful or element vanished.")
                return True # Optimistic: if stale after potential delete actions, assume it worked or is gone
            except ElementClickInterceptedException as eci:
                print(f"    [ERROR] Element click intercepted for article {i+1}: {str(eci).splitlines()[0]}.")
                driver.save_screenshot(f"debug_CLICK_INTERCEPTED_article_{i+1}.png")
                try:
                    driver.find_element(By.XPATH, "//body").send_keys(Keys.ESCAPE)
                    time.sleep(1)
                except: pass
                continue 
            except TimeoutException as te:
                print(f"    [ERROR] TimeoutException during article {i+1} processing: {str(te).splitlines()[0]}")
                driver.save_screenshot(f"debug_TIMEOUT_article_{i+1}.png")
                try:
                    driver.find_element(By.XPATH, "//body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                except: pass
                continue
            except Exception as e:
                print(f"    [ERROR] An unexpected error occurred while trying to delete article {i+1}: {e}")
                driver.save_screenshot(f"debug_UNEXPECTED_ERROR_article_{i+1}.png")
                try:
                    driver.find_element(By.XPATH, "//body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                except: pass
                continue
        # End of the for loop for articles
        
        print("  [INFO] Checked all visible articles in this pass, none were successfully deleted OR all threw an exception before the delete click.")
        return False # If loop finishes without returning True

    # This except block is for the outer try in the function
    except Exception as e:
        print(f"[FATAL ERROR] Major error in attempt_single_reply_delete function itself: {e}")
        driver.save_screenshot("debug_major_error_attempt_single_reply_delete.png")
        return False


if __name__ == "__main__":
    if not all([TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_PROFILE_NAME]):
        print("Critical Error: Missing TWITTER_USERNAME, TWITTER_PASSWORD, or TWITTER_PROFILE_NAME in .env file. Exiting.")
        exit()

    driver = None # Initialize driver to None for the finally block
    total_deleted_session = 0
    
    try:
        driver = setup_driver()
        if login_to_twitter(driver, TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_VERIFICATION_INPUT):
            if navigate_to_profile_with_replies(driver, TWITTER_PROFILE_NAME):
                consecutive_scrolls_without_delete = 0 
                for iteration in range(MAX_TOTAL_ITERATIONS):
                    print(f"\n--- Iteration {iteration + 1}/{MAX_TOTAL_ITERATIONS} ---")
                    print(f"    Scrolls w/o delete: {consecutive_scrolls_without_delete}, Total deleted: {total_deleted_session}")
                    
                    deleted_in_this_pass = attempt_single_reply_delete(driver)

                    if deleted_in_this_pass:
                        total_deleted_session += 1
                        consecutive_scrolls_without_delete = 0 
                        print(f"Successfully deleted a tweet/reply. Total for session: {total_deleted_session}")
                        if total_deleted_session >= MAX_DELETES_PER_SESSION:
                            print(f"Reached session limit of {MAX_DELETES_PER_SESSION} deletes.")
                            break
                        # Small pause before next action even if it's not a scroll
                        time.sleep(random.uniform(DELAY_BETWEEN_ACTIONS_MIN / 2, DELAY_BETWEEN_ACTIONS_MAX / 2))
                    else:
                        print("No tweet/reply deleted in this attempt pass. Will scroll.")
                        consecutive_scrolls_without_delete += 1
                        if consecutive_scrolls_without_delete >= MAX_SCROLL_ATTEMPTS_WITHOUT_DELETE:
                            print(f"Failed to delete anything for {MAX_SCROLL_ATTEMPTS_WITHOUT_DELETE} consecutive scroll attempts. Ending session.")
                            break
                        
                        old_page_height = driver.execute_script("return document.body.scrollHeight")
                        scroll_down(driver)
                        time.sleep(1.5) # Wait for content to load after scroll
                        new_page_height = driver.execute_script("return document.body.scrollHeight")
                        
                        # Check for end of content
                        if new_page_height == old_page_height and consecutive_scrolls_without_delete > 2: # If height hasn't changed after a few scrolls
                            current_scroll_y = driver.execute_script("return window.pageYOffset")
                            total_scrollable_height = driver.execute_script("return document.body.scrollHeight - window.innerHeight")
                            if abs(current_scroll_y - total_scrollable_height) < 15 : # If very close to the bottom
                                print("Page height not changing and near bottom after multiple scrolls. Assuming end of content.")
                                break
            else:
                print("Failed to navigate to profile page. Cannot proceed.")
        else:
            print("Login failed. Cannot proceed.")

    except KeyboardInterrupt:
        print("\nScript interrupted by user (Ctrl+C).")
    except Exception as e:
        print(f"An unexpected critical error occurred in the main execution block: {e}")
        if driver:
             driver.save_screenshot("main_execution_critical_error.png")
             print(f"Current URL at time of error: {driver.current_url}")
    finally:
        print(f"\n--- Session Summary ---")
        print(f"Total tweets/replies deleted in this session: {total_deleted_session}")
        if driver:
            input("Automation finished or encountered an error. Review the console. Press Enter to close the browser...")
            driver.quit()
        else:
            print("Driver was not initialized or an early error occurred.")