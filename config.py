import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = 'stocker-secret-key-2024'
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None
    AWS_REGION = 'us-east-1'
    