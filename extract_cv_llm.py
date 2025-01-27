import os
import random
import string
from dotenv import load_dotenv
from classes.file_manager import FileManager
from classes.azure_blob_manager import AzureBlobManager
from classes.azure_document_intelligence import AzureDocIntel
from classes.langchain_chunk_manager import LangchainChunkManager
from classes.langchain_llm import LangchainLLMManager
from classes.audit_log_manager import LogManager

#References:
#https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api?view=doc-intel-4.0.0&pivots=programming-language-rest-api
#https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&preserve-view=true&tabs=windows&pivots=programming-language-rest-api


#load the env file
load_dotenv()

#invoke the logger with a random string of length 8
random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
log_manager = LogManager(unique_key = random_string)
app_logging = log_manager.get_logger()

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

# azure openai variables
azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_openai_deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
azure_openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
azure_openai_temperature = os.environ.get("AZURE_OPENAI_TEMPERATURE")
#azure_openai_max_tokens_per_minute = os.environ.get("AZURE_OPENAI_MAX_TOKENS_PER_MINUTE") #TODO: use this


#do all the vision tasks in here
def azure_vision(file_name, file_type, data, prompt, app_logging):
    #instantiate class which will get a token
    blob_manager = AzureBlobManager(
        endpoint_url = azure_storage_endpoint_url,
        tenant_id = azure_storage_tenant_id,
        grant_type = azure_storage_grant_type,
        client_id = azure_storage_client_id,
        client_secret = azure_storage_client_secret,
        scope = azure_storage_scope,
        file_name=file_name,
        app_logging = app_logging
    )
    
    #upload file to azure storage
    blob_manager.upload_file(azure_storage_account_url, 
                            azure_storage_account_container_name, 
                            azure_storage_account_prefix, 
                            file_type,
                            data,
                            azure_storage_file_tags
    )

    #get user delegation sas token
    sas_token = blob_manager.get_user_delegated_sas_token(azure_storage_account_url,
                                                        azure_storage_account_container_name,
                                                        azure_storage_account_prefix,
                                                        azure_storage_sas_valid_hours
    )

    #get the ocr data by passing in the sas token (the URL of the file)
    ocr_manager= AzureDocIntel(azure_vision_full_endpoint, 
                               azure_vision_headers, 
                               sas_token, 
                               app_logging
    )
    ocr_response, ocr_text = ocr_manager.get_ocr_text()

    #get chunked data from langchain
    if ocr_response is not None:
        lanchain_manager = LangchainChunkManager(ocr_text, "text", app_logging)
        langchain_text = lanchain_manager.process()

        #get the llm response
        llm_response = ""
        if langchain_text is not None:
            for t in langchain_text:
                app_logging.debug("In langchain_text loop")
                #get response from LLM
                llm_manager = LangchainLLMManager(
                    prompt,
                    t,
                    azure_openai_endpoint,
                    azure_openai_deployment_name,
                    azure_openai_api_version,
                    azure_openai_key,
                    azure_openai_temperature,
                    None,
                    app_logging
                )
                cv_data = llm_manager.generate_response()

                #concatenate the responses
                llm_response = llm_response + cv_data
            return llm_response
        else:
            return None


#Start
prompt = ""
file_name = "c:\\temp\\cv_llm_app\\1.png"

#read the prompt.txt file
try:
    with open("prompt.txt", "r") as f:
        prompt = f.read()
except Exception as e:
    app_logging.error("Error reading prompt file. Going to exit.")
    exit(1)

#get file type and get the file contents
file_manager = FileManager(file_name, app_logging)
file_type, file_contents = file_manager.get_file_type_and_contents()

#do all the vision and llm things
if file_type in ['application/pdf', 'image/jpeg', 'image/png']:
    cv_details = azure_vision(file_name, file_type, file_contents, prompt, app_logging)
    with open("cv_details_output\\cv_details.json", "w") as f:
        f.write(cv_details)
        
else:
    app_logging.error("CV file type could not be determined or not valid.")
    exit(1)

