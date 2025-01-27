from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage

class LangchainLLMManager:
    def __init__(self, prompt, text, endpoint, deployment_name, api_version, key, temperature, max_tokens, app_logger):
        self.prompt = prompt
        self.text = text
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.key = key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.app_logger = app_logger

        #get an instance of the azure OpenAI LLM
        self.llm = self._initialize_llm()

    
    def _initialize_llm(self):
        try:
            return AzureChatOpenAI(
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                azure_deployment=self.deployment_name,
                openai_api_key=self.key,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            self.app_logger.error(f"Error initializing LLM: {e}")
            return None

    
    #generate a response from the LLM using the provided prompt and text
    def generate_response(self):
        try:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prompt.replace("{","").replace("}","")),
                ("human", "{input}")
            ])

            #give the user input which will be the CV data
            formatted_prompt = prompt_template.format_prompt(input=self.text)
            response = self.llm([HumanMessage(content=formatted_prompt.to_string())])
            return response.content
        except Exception as e:
            self.app_logger.error(f"Error generating LLM response: {e}")
            return None