from supabase import create_client
from dotenv import load_dotenv
import os
load_dotenv()
SECRET_URL = os.getenv("SUPABASE_URL")
SECRET_KEY = os.getenv("SUPABASE_KEY")

print(SECRET_KEY)
print(SECRET_URL)

supabase = create_client(SECRET_URL, SECRET_KEY)    