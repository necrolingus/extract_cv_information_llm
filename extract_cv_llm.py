import io
import os
import magic
from PIL import Image
from dotenv import load_dotenv
from classes.file_manager import FileManager
from classes.azure_blob_manager import AzureBlobManager
from classes.azure_document_intelligence import AzureDocIntel


#References:
#https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api?view=doc-intel-4.0.0&pivots=programming-language-rest-api
#https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&preserve-view=true&tabs=windows&pivots=programming-language-rest-api


#load the env file
load_dotenv()

# azure vision variables
azure_vision_endpoint = os.environ.get("AZURE_VISION_ENDPOINT")
azure_vision_key = os.environ.get("AZURE_VISION_KEY")
azure_vision_model_id = os.environ.get("AZURE_VISION_MODEL_ID")
azure_vision_headers = {
    "Content-Type": "application/json",
    "Ocp-Apim-Subscription-Key": f"{azure_vision_key}"
}
azure_vision_full_endpoint = f"{azure_vision_endpoint}documentintelligence/documentModels/{azure_vision_model_id}:analyze?api-version=2024-11-30"

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
    sas_token = blob_manager.get_user_delegated_sas_token(azure_storage_account_url,
                                                   azure_storage_account_container_name,
                                                   azure_storage_account_prefix,
                                                   file_name,
                                                   azure_storage_sas_valid_hours
    )

    #give the sas token to the azure vision class to it can OCR it and save the text
    ocr_job = AzureDocIntel(azure_vision_full_endpoint, azure_vision_headers, sas_token)
    print(ocr_job.get_ocr_text())


#Start
#get file type and process the file
file_name = "2.png"
file_manager = FileManager(file_name)
file_type, file_contents = file_manager.get_file_type_and_contents()

if file_type not in ['aplication/pdf']:
    print(f"File is an image of type: {file_type}")
    azure_vision(file_name, file_type, file_contents)
