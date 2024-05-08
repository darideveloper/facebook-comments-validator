import os
from dotenv import load_dotenv
from libs.validator import Validator

load_dotenv()
VAR = os.getenv("VAR")

if __name__ == "__main__":
    validator = Validator()
    validator.__loop_facebook_posts__()
    print()