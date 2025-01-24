import io
import os
import magic
from PIL import Image
from dotenv import load_dotenv
from classes.azure_blob_manager import AzureBlobManager
import sys

#References:
#https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&preserve-view=true&tabs=windows&pivots=programming-language-rest-api

#load the env file
load_dotenv()

# azure vision variables
azure_vision_endpoint = os.environ.get("AZURE_VISION_ENDPOINT")
azure_vision_key = os.environ.get("AZURE_VISION_KEY")
azure_vision_model_id = os.environ.get("AZURE_VISION_MODEL_ID")
headers = {
    "Content-Type": "application/json",
    "Ocp-Apim-Subscription-Key": azure_vision_key,
}

# azure auth variables
azure_storage_endpoint_url = os.environ.get("AZURE_STORAGE_ENDPOINT_URL")
azure_storage_tenant_id = os.environ.get("AZURE_STORAGE_TENANT_ID")
azure_storage_grant_type = os.environ.get("AZURE_STORAGE_GRANT_TYPE")
azure_storage_client_id = os.environ.get("AZURE_STORAGE_CLIENT_ID")
azure_storage_client_secret = os.environ.get("AZURE_STORAGE_CLIENT_SECRET")
azure_storage_scope = os.environ.get("AZURE_STORAGE_SCOPE")

# azure storage variables
azure_storage_account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
azure_storage_account_container_name = os.environ.get("AZURE_STORAGE_ACCOUNT_CONTAINER_NAME")
azure_storage_account_prefix = os.environ.get("AZURE_STORAGE_ACCOUNT_PREFIX")
azure_storage_file_tags = os.environ.get("AZURE_STORAGE_FILE_TAGS")
azure_storage_sas_valid_hours = int(os.environ.get("AZURE_STORAGE_SAS_VALID_HOURS"))


#read file from disk
def read_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            return data
    except Exception as e:
        print(f"Could not read the file: {e}")
        return None


#check if the file is an image using pillow for accurate checking
def check_if_image(data):
    try:
        image = Image.open(io.BytesIO(data))
        file_type = image.format.lower()
        if file_type in ['png']:
            return 'image/png'
        elif file_type in ['jpeg', 'jpg']:
            return 'image/jpeg'
        return None
    except Exception as e:
        print(f"Could not determine image type: {e}")
        return None


#check if file type is a PDF using magic library
def check_if_pdf(data):
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(data)
        if file_type == 'application/pdf':
            return 'application/pdf'
        return None
    except Exception as e:
        print(f"Could not determine if PDF: {e}")
        return None
    

#do all the vision tasks in here
def azure_vision(file_name, file_type, data):
    #instantiate class which will get a token
    blob_manager = AzureBlobManager(
        endpoint_url = azure_storage_endpoint_url,
        tenant_id = azure_storage_tenant_id,
        grant_type = azure_storage_grant_type,
        client_id = azure_storage_client_id,
        client_secret = azure_storage_client_secret,
        scope = azure_storage_scope
    )
    
    #upload file to azure storage
    blob_manager.upload_file(azure_storage_account_url, 
                            azure_storage_account_container_name, 
                            azure_storage_account_prefix, 
                            file_name, 
                            file_type,
                            data,
                            azure_storage_file_tags
    )

    #get user delegation sas token
    blob_manager.get_user_delegated_sas_token_key(azure_storage_account_url,
                                                   azure_storage_account_container_name,
                                                   azure_storage_account_prefix,
                                                   file_name,
                                                   azure_storage_sas_valid_hours
    )
   


#check the type of the file
file_name = "1.jpg"
data = read_file(file_name)
if data:
    file_type = check_if_image(data)
    if file_type:
        print(f"File is an image of type: {file_type}")
        azure_vision(file_name, file_type, data)
    else:
        is_pdf = check_if_pdf(data)
        if is_pdf:
            print(is_pdf)
            azure_vision(file_name, file_type, data)
