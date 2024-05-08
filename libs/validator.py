import os
from selenium import webdriver
from libs.xlsx import SpreadsheetManager
from dotenv import load_dotenv

load_dotenv()
EXCEL_PATH = os.getenv("EXCEL_PATH")
SHEET_NAME = os.getenv("SHEET_NAME")

class Validator():
    
    def __init__(self):
        
        self.browser = None
        self.xlsx = None
        self.excel_data = None
        
        self.__start_browser__()
        self.__load_excel_data__()
                
    def __start_browser__(self):
        """ Start and setup firefox browser
        """
        
        # Instance browser
        print("Opening browser...")
        self.browser = webdriver.Firefox()
        self.browser.get("https://www.google.com")
    
    def __load_excel_data__(self):
        """ Load and filter excel data
        """
        
        # Instance xlsx and read data
        base_file_name = os.path.basename(EXCEL_PATH)
        print(f"Reading excel file '{base_file_name}' in sheet '{SHEET_NAME}'...")
        self.xlsx = SpreadsheetManager(EXCEL_PATH)
        self.xlsx.set_sheet(SHEET_NAME)
        excel_data = self.xlsx.get_data()
        
        # Filter excel data
        self.excel_data = list(filter(
            lambda row: row[6].lower().strip() == "odio",
            excel_data[1:]
        ))
    
    def __loop_facebook_posts__(self):
        """ Loop each register from excel data
        """
        
        for row in self.excel_data:
            comment = row[0]
            link = row[1]
            comment_short = comment if len(comment) < 50 else comment[:50] + "..."
            print(f"Validating comment '{comment_short}'...")
            self.__validate_comment__(comment_short, link)
    
    def __validate_comment__(self, comment: str, link: str):
        """ Check if comment is in the post

        Args:
            comment (str): comment to check
            link (str): facebook post link
        """
        self.browser.get(link)
        print()