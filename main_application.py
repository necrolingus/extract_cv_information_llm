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


class Application:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Setup logger
        self.log_manager = LogManager(unique_key=self._generate_random_key())
        self.app_logging = self.log_manager.get_logger()
        
        # Initialize Azure configurations
        self.config_variables = self._load_config_variables()
    
    
    #generate random string for log tracing
    def _generate_random_key(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    
    #load all config variables
    def _load_config_variables(self):
        return {
            "azure_vision_endpoint": os.environ.get("AZURE_VISION_ENDPOINT"),
            "azure_vision_key": os.environ.get("AZURE_VISION_KEY"),
            "azure_vision_model_id": os.environ.get("AZURE_VISION_MODEL_ID"),
            "azure_vision_headers": {
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": f"{os.environ.get("AZURE_VISION_KEY")}"
            },
            "azure_vision_full_endpoint": f"{os.environ.get("AZURE_VISION_ENDPOINT")}documentintelligence/documentModels/{os.environ.get("AZURE_VISION_MODEL_ID")}:analyze?api-version=2024-11-30",
            # azure auth variables
            "azure_storage_endpoint_url": os.environ.get("AZURE_STORAGE_ENDPOINT_URL"),
            "azure_storage_tenant_id": os.environ.get("AZURE_STORAGE_TENANT_ID"),
            "azure_storage_grant_type": os.environ.get("AZURE_STORAGE_GRANT_TYPE"),
            "azure_storage_client_id": os.environ.get("AZURE_STORAGE_CLIENT_ID"),
            "azure_storage_client_secret": os.environ.get("AZURE_STORAGE_CLIENT_SECRET"),
            "azure_storage_scope": os.environ.get("AZURE_STORAGE_SCOPE"),
            # azure storage variables
            "azure_storage_account_url": os.environ.get("AZURE_STORAGE_ACCOUNT_URL"),
            "azure_storage_account_container_name": os.environ.get("AZURE_STORAGE_ACCOUNT_CONTAINER_NAME"),
            "azure_storage_account_prefix": os.environ.get("AZURE_STORAGE_ACCOUNT_PREFIX"),
            "azure_storage_file_tags": os.environ.get("AZURE_STORAGE_FILE_TAGS"),
            "azure_storage_sas_valid_hours": int(os.environ.get("AZURE_STORAGE_SAS_VALID_HOURS")),
            # azure openai variables
            "azure_openai_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
            "azure_openai_deployment_name": os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "azure_openai_api_version": os.environ.get("AZURE_OPENAI_API_VERSION"),
            "azure_openai_key": os.environ.get("AZURE_OPENAI_KEY"),
            "azure_openai_temperature": os.environ.get("AZURE_OPENAI_TEMPERATURE"),
            #"azure_openai_max_tokens_per_minute": os.environ.get("AZURE_OPENAI_MAX_TOKENS_PER_MINUTE") #TODO: use this
        }
    

    def process_files(self, file_name, prompt_file):
        """Process the file by reading and analyzing it."""
        # Read the prompt
        prompt = self._read_prompt(prompt_file)
        
        # Get file details
        file_manager = FileManager(file_name, self.app_logging)
        file_type, file_contents = file_manager.get_file_type_and_contents()
        
        # Process vision and LLM if valid file type
        if file_type in ['application/pdf', 'image/jpeg', 'image/png']:
            cv_details = self._azure_vision(file_name, file_type, file_contents, prompt)
            if cv_details is not None:
                self._save_cv_details(cv_details)
        else:
            self.app_logging.error("CV file type could not be determined or not valid.")
            exit(1)
    
    
    #read the LLM prompt text file
    def _read_prompt(self, prompt_file_path):
        try:
            with open(prompt_file_path, "r") as f:
                return f.read()
        except Exception as e:
            self.app_logging.error(f"Error reading prompt file. {e}")
            exit(1)
       
    
    #handle the vision processing
    def _azure_vision(self, file_name, file_type, data, prompt):
        #instantiate AzureBlobManager
        blob_manager = AzureBlobManager(endpoint_url = self.config_variables["azure_storage_endpoint_url"],
                                        tenant_id = self.config_variables["azure_storage_tenant_id"],
                                        grant_type = self.config_variables["azure_storage_grant_type"],
                                        client_id = self.config_variables["azure_storage_client_id"],
                                        client_secret = self.config_variables["azure_storage_client_secret"],
                                        scope = self.config_variables["azure_storage_scope"],
                                        file_name=file_name,
                                        app_logging = self.app_logging)
        
        #upload the CV file to Azure Storage
        blob_manager.upload_file(self.config_variables["azure_storage_account_url"], 
                                self.config_variables["azure_storage_account_container_name"], 
                                self.config_variables["azure_storage_account_prefix"], 
                                file_type,
                                data,
                                self.config_variables["azure_storage_file_tags"])
        
        #get the SAS token URL
        sas_token = blob_manager.get_user_delegated_sas_token(self.config_variables["azure_storage_account_url"],
                                                        self.config_variables["azure_storage_account_container_name"],
                                                        self.config_variables["azure_storage_account_prefix"],
                                                        self.config_variables["azure_storage_sas_valid_hours"])

        
        #instantiate AzureDocIntel for OCR 
        ocr_manager = AzureDocIntel(self.config_variables["azure_vision_full_endpoint"],
                                    self.config_variables["azure_vision_headers"],
                                    sas_token,
                                    self.app_logging)
        
        #get ocr data
        ocr_response, ocr_text = ocr_manager.get_ocr_text()

        #process chunking and LLM response
        if ocr_text:
            llm_text = self._langchain_chunking(ocr_text, prompt)
            return llm_text
        return None
    
    
    #get text to pass to LLM using langchain
    def _langchain_chunking(self, ocr_text, prompt):
        langchain_manager = LangchainChunkManager(ocr_text, "text", self.app_logging)
        langchain_text = langchain_manager.process()
        
        if langchain_text:
            llm_response = self._get_llm_response(langchain_text, prompt)
            return llm_response
        return None

    
    #get LLM response
    def _get_llm_response(self, langchain_text, prompt):
        llm_response = ""
        for text in langchain_text:
            llm_manager = LangchainLLMManager(prompt,
                                            text,
                                            self.config_variables["azure_openai_endpoint"],
                                            self.config_variables["azure_openai_deployment_name"],
                                            self.config_variables["azure_openai_api_version"],
                                            self.config_variables["azure_openai_key"],
                                            self.config_variables["azure_openai_temperature"],
                                            None,
                                            self.app_logging)

            llm_response += llm_manager.generate_response()
        return llm_response
    

    #save the cv response from the LLM
    def _save_cv_details(self, cv_details):
        """Save the CV details output to a file."""
        with open("cv_details_output\\cv_details.json", "w") as f:
            f.write(cv_details)


# Start processing
if __name__ == "__main__":
    app = Application()
    app.process_files("c:\\temp\\cv_llm_app\\1.png", "prompt.txt")