import io
import magic
from PIL import Image


class FileManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_type = None

    
    #get and thenreturn the file type
    def get_file_type_and_contents(self):
        file_contents = self.read_file()
        if file_contents is not None:
            self.file_type = self.check_if_image(file_contents)
            if self.file_type is None:
                self.file_type = self.check_if_pdf(file_contents)
        return self.file_type, file_contents

    
    #read file from disk
    def read_file(self):
        try:
            with open(self.file_path, 'rb') as f:
                data = f.read()
                return data
        except Exception as e:
            print(f"Could not read the file: {e}")
            return None

    
    #check if the file is an image using Pillow for accurate checking
    def check_if_image(self, data):
        try:
            image = Image.open(io.BytesIO(data))
            file_type = image.format.lower()
            if file_type == 'png':
                return 'image/png'
            elif file_type in ['jpeg', 'jpg']:
                return 'image/jpeg'
            return None
        except Exception as e:
            print(f"Could not determine image type: {e}")
            return None

    
    #check if file type is a PDF using the magic library
    def check_if_pdf(self, data):
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_buffer(data)
            if file_type == 'application/pdf':
                return 'application/pdf'
            return None
        except Exception as e:
            print(f"Could not determine if PDF: {e}")
            return None
