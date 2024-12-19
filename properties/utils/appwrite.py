import os
import tempfile
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from appwrite.id import ID
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppwriteHelper:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
        self.client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        self.client.set_key(os.getenv('APPWRITE_API_KEY'))
        self.storage = Storage(self.client)
        print(f"{os.getenv('APPWRITE_ENDPOINT')} {os.getenv('APPWRITE_BUCKET_ID')} {os.getenv('APPWRITE_API_KEY')} {os.getenv('APPWRITE_PROJECT_ID')}")
    
    def upload_file(self, file, user_id):
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            input_file = InputFile.from_path(temp_file_path)
            result = self.storage.create_file(
                bucket_id=os.getenv('APPWRITE_BUCKET_ID'),
                file_id=ID.unique(),
                file=input_file
            )

            print("File uploaded successfully:", result)
            print(f"{os.getenv('APPWRITE_ENDPOINT')} {os.getenv('APPWRITE_BUCKET_ID')} {os.getenv('APPWRITE_API_KEY')} {os.getenv('APPWRITE_PROJECT_ID')}")
            
            file_url = f"{os.getenv('APPWRITE_ENDPOINT')}/storage/buckets/{os.getenv('APPWRITE_BUCKET_ID')}/files/{result['$id']}/view?project={os.getenv('APPWRITE_PROJECT_ID')}"
            return file_url
            
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)