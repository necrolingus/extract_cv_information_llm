import requests
import time


class AzureDocIntel:
    def __init__(self, full_endpoint, headers, sas_token):
        self.full_endpoint = full_endpoint
        self.headers = headers
        self.sas_token = sas_token
        self.payload = {"urlSource": self.sas_token}


    def get_ocr_text(self):
        try:
            response = requests.post(self.full_endpoint, headers=self.headers, json=self.payload)
            time.sleep(5)

            #Call the returned endpoint in the operation location header until the status is no longer running
            ocr_outcome = requests.get(response.headers.get('Operation-Location'), headers=self.headers)
            while ocr_outcome.json().get("status") not in ['succeeded']:
                print("wiating 5 seconds for ocr data....")
                time.sleep(5)
                ocr_outcome = requests.get(response.headers.get('Operation-Location'), headers=self.headers)
            
            text_only = ocr_outcome.json().get("analyzeResult").get("content")
            return response, text_only
        
        except Exception as e:
            print(f"Error getting OCR text: {e}")
            return None, None

