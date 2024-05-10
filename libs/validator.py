import os
from time import sleep
from selenium import webdriver
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from tqdm import tqdm
import pandas as pd


load_dotenv()
EXCEL_PATH = os.getenv("EXCEL_PATH")
SHEET_NAME = os.getenv("SHEET_NAME")


class Validator():
    
    def __init__(self):
        
        self.browser = None
        self.xlsx = None
        self.dataframe = None
        
        self.__start_browser__()
        self.__load_excel_data__()
        
    def __refresh__(self):
        """ Refresh browser with tabs """
        
        # Refresh selenium
        self.browser.execute_script("window.open('');")
        windows = self.browser.window_handles
        self.browser.switch_to.window(windows[len(windows) - 1])
        sleep(1.5)
        self.browser.close()
        self.browser.switch_to.window(windows[0])
        sleep(1.5)
                
    def __start_browser__(self):
        """ Start and setup firefox browser
        """
        
        # Instance browser
        print("Opening browser...")
        self.browser = webdriver.Firefox()
    
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
        
        print("Validating comments...")
        comments_found = 0
        comments_not_found = 0
        for index, row in tqdm(self.dataframe.iterrows(), total=len(self.dataframe)):
            comment = row["TEXTO A ANALIZAR"]
            link = row["URL"]
            odio = row["ODIO"]
            text_type = row["TIPO DE MENSAJE"]
            
            if odio == "no odio":
                continue
            
            if text_type == "Comment":
                comment_short = comment if len(comment) < 50 else comment[:50] + "..."
                found_text = self.__validate_comment__(comment_short, link)
                if found_text == "si":
                    comments_found += 1
                else:
                    comments_not_found += 1
            else:
                found_text = "no es comentario"
               
            # Update cell value
            self.dataframe.at[index, "Comentario encontrado"] = found_text
            
            # Save excel
            self.dataframe.to_excel(EXCEL_PATH, index=False, sheet_name=SHEET_NAME)
    
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
            "comments": '.displayed > div:nth-child(n+5)[data-comp-id] '
                        '[style="color:#000000;"]',
        }
        
        try:
            # Load page
            self.browser.get(link)
            
            # Close facebook login
            self.browser.find_element(By.CSS_SELECTOR, selectors["close"]).click()
            self.__refresh__()
        except Exception:
            return "error al cargar la página"
        self.__refresh__()
        
        # Get page comments
        comments = self.browser.find_elements(By.CSS_SELECTOR, selectors["comments"])
        comments_texts = [comment.text for comment in comments]
        comments_texts = [
            text.lower().strip().replace(",", "") for text in comments_texts
        ]
        
        # Validate comment in the page
        if comment in comments_texts:
            return "si"
        else:
            return "no"