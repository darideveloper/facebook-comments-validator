import os
import threading
from time import sleep
from selenium import webdriver
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
import pandas as pd


load_dotenv()
EXCEL_PATH = os.getenv("EXCEL_PATH")
SHEET_NAME = os.getenv("SHEET_NAME")

is_running = True


class Validator():
    
    def __init__(self):
        
        self.browser = None
        self.xlsx = None
        self.dataframe = None
        self.lock = threading.Lock()
        
        self.__start_browser__()
        self.__load_excel_data__()
        
        self.comments_found = 0
        self.comments_not_found = 0
        self.no_comments = 0
        
    def __refresh__(self):
        """ Refresh browser with tabs """
        
        self.browser.execute_script("window.open('');")
        windows = self.browser.window_handles
        self.browser.switch_to.window(windows[len(windows) - 1])
        sleep(1.5)
        self.browser.close()
        self.browser.switch_to.window(windows[0])
        sleep(1.5)
        
    def __move_new_tab__(self):
        """ Create and move to new tab, and delete the last one """
        
        self.browser.execute_script("window.open('');")
        self.browser.close()
        windows = self.browser.window_handles
        self.browser.switch_to.window(windows[0])
                
    def __start_browser__(self):
        """ Start and setup firefox browser
        """
        
        # Private window option
        options = webdriver.FirefoxOptions()
        options.add_argument("--private-window")
        
        # Instance browser
        print("Opening browser...")
        self.browser = webdriver.Firefox(options=options)
    
    def __load_excel_data__(self):
        """ Load and filter excel data
        """
        
        # Instance xlsx and read data
        base_file_name = os.path.basename(EXCEL_PATH)
        print(f"Reading excel file '{base_file_name}' in sheet '{SHEET_NAME}'...")
        self.dataframe = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        
        # Add column "Comentario encontrado" if not exists
        self.dataframe["Comentario encontrado"] = [""] * len(self.dataframe)
    
    def __loop_facebook_posts__(self):
        """ Loop each register from excel data
        """
                
        print("Validating comments")
        for index, row in self.dataframe.iterrows():
                        
            # End thread loop
            global lock
            with lock:
                if not is_running:
                    print("Stopped")
                    break
            
            comment = row["TEXTO A ANALIZAR"]
            link = row["URL"]
            odio = row["ODIO"]
            text_type = row["TIPO DE MENSAJE"]
            print(f"Validating comment {index + 1}/{len(self.dataframe)}")
            
            if odio == "no odio":
                continue
            
            if text_type == "Comment":
                found_text = self.__validate_comment__(comment, link)
                if found_text == "si":
                    self.comments_found += 1
                else:
                    self.comments_not_found += 1
            else:
                found_text = "no es comentario"
                self.no_comments += 1
               
            # Update cell value
            self.dataframe.at[index, "Comentario encontrado"] = found_text
            
        # Save excel
        print("Saving excel file...")
        self.dataframe.to_excel(EXCEL_PATH, index=False, sheet_name=SHEET_NAME)
        print("Excel file saved")
    
    def __validate_comment__(self, comment: str, link: str) -> str:
        """ Check if comment is in the post

        Args:
            comment (str): comment to check
            link (str): facebook post link
            row (list): excel row data
            
        Returns:
            str: "si" if comment is in the post, "no" otherwise
                 and "error al cargar la página" if error
        """
        
        selectors = {
            "close": '.bg-s8 > div:nth-child(2) > div:nth-child(1) > '
                     'div:nth-child(1) > div:nth-child(2)',
            "comments": '[data-timeout="30"] [style="color:#000000;"]',
        }
        
        try:
            # Load page
            self.__move_new_tab__()
            self.browser.get(link)
            self.__refresh__()
            
            # Close facebook login
            self.browser.find_element(By.CSS_SELECTOR, selectors["close"]).click()
            self.__refresh__()
        except Exception:
            return "error al cargar la página"
        
        # Get page comments
        clean_chars = [
            "\n",
            "\t",
            "\r",
            ",",
            ".",
            "...",
            "?",
            "!",
            "¡",
            "¿",
            "(",
            ")",
            ":",
            ";",
            '"',
            "'",
            " ",
        ]
        comments = self.browser.find_elements(By.CSS_SELECTOR, selectors["comments"])
        comments_texts = [comment.text for comment in comments]
        comments_texts_clean = []
        for comment_text in comments_texts:
            
            # Remove extra chars
            for char in clean_chars:
                comment_text = comment_text.replace(char, "")

            # remove emojis
            comment_text = comment_text.encode('ascii', 'ignore').decode('ascii')
            
            comments_texts_clean.append(comment_text.lower().strip())
        
        # Validate comment in the page
        comment = comment.replace(" ", "")
        if comment in comments_texts_clean:
            return "si"
        else:
            return "no"
        
    def __end_thread__(self):
        """ End thread
        """
        
        global is_running
        global lock
        lock = threading.Lock()
        
        while True:
            option = input("Press 'q' to stop: \n")
            if option == "q":
                with lock:
                    
                    # Change running status
                    is_running = False
                    
                    # Show counters
                    print(f"Comments found: {self.comments_found}")
                    print(f"Comments not found: {self.comments_not_found}")
                    print(f"No comments: {self.no_comments}")
                    print("Stopping...")
                    
                    break
        
    def autorun(self):
        
        # Lock and thread
        thread = threading.Thread(
            target=self.__loop_facebook_posts__,
        )
        thread.start()
        self.__end_thread__()
        thread.join()