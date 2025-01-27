from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from io import BytesIO


class LangchainManager:
    def __init__(self, file_contents, file_type):
        """
        Initialize LangchainManager.

        :param file_contents: The binary contents of the file (PDF or text).
        :param file_type: The type of the input ("pdf" or "text").
        """
        self.file_contents = file_contents
        self.file_type = file_type

    
    #get text from PDF binary contents
    def _extract_text_from_pdf(self):
        loader = PyPDFLoader(BytesIO(self.file_contents))
        documents = loader.load()
        return " ".join([doc.page_content for doc in documents])

    
    #slit text to make it manageable for the LLM
    def _split_text(self, text):
        splitter = RecursiveCharacterTextSplitter(chunk_size=20000, chunk_overlap=2000, separators=["\n", ". "])
        return splitter.split_text(text)

    
    #prepare the input data for the LLM
    def process(self):
        if self.file_type == "application/pdf":
            text = self._extract_text_from_pdf()
        elif self.file_type == "text":
            text = self.file_contents
        else:
            raise ValueError("Unsupported file type.")

        return self._split_text(text)