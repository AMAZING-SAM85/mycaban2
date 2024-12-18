import os
import tempfile
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from appwrite.id import ID
from django.conf import settings

class AppwriteHelper:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(settings.APPWRITE_ENDPOINT)
        self.client.set_project(settings.APPWRITE_PROJECT_ID)
        self.client.set_key(settings.APPWRITE_API_KEY)
        self.storage = Storage(self.client)
    
    def upload_file(self, file, user_id):
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            input_file = InputFile.from_path(temp_file_path)
            result = self.storage.create_file(
                bucket_id=settings.APPWRITE_BUCKET_ID,
                file_id=ID.unique(),
                file=input_file
            )
            
            file_url = f"{settings.APPWRITE_ENDPOINT}/storage/buckets/{settings.APPWRITE_BUCKET_ID}/files/{result['$id']}/view?project={settings.APPWRITE_PROJECT_ID}"
            return file_url
            
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
