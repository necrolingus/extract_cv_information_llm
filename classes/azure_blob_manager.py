import requests
import time
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from classes.azure_generate_user_delegated_sas_token import userDelegatedSasToken


class AzureBlobManager:
  def __init__(self, endpoint_url, tenant_id, grant_type, client_id, client_secret, scope):
    self.endpoint_url = endpoint_url
    self.tenant_id = tenant_id
    self.grant_type = grant_type
    self.client_id = client_id
    self.client_secret = client_secret
    self.scope = scope
    self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    self.token = None
    self.token_expiry = None
    self._refresh_token() # Get the token during initialization
    

  def _refresh_token(self):
    """Fetch a new token and update expiry."""
    payload = {
        'grant_type': self.grant_type,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'scope': self.scope
    }
    response = requests.post(f"{self.endpoint_url}{self.tenant_id}/oauth2/v2.0/token", headers=self.headers, data=payload)

    token_data = response.json()
    self.token = token_data.get('access_token')
    expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour if not provided
    self.token_expiry = time.time() + expires_in - 60  # Refresh 1 minute before expiry
  

  def _get_token(self):
    """Ensure the token is valid and return it."""
    if self.token is None or time.time() >= self.token_expiry:
        self._refresh_token()
    return self.token

    
  def upload_file(self, storage_url, container_name, prefix, file_name, file_type, data, azure_storage_file_tags):
    url = f"{storage_url}{container_name}/{prefix}/{file_name}"
    headers = {
      'Authorization': f'Bearer {self._get_token()}',
      'x-ms-blob-type': 'BlockBlob',
      'x-ms-version': '2020-04-08',
      'x-ms-tags': azure_storage_file_tags,
      'Content-Type': file_type
    }
    response = requests.put(url, headers=headers, data=data)
    return response

  
  def get_user_delegated_sas_token(self, storage_url, container_name, prefix, file_name, delegation_key_valid_hours):
    """
      This function will first get the user delegation key, and then call class generate_user_delegated_sas_token
      to generate the SAS token that will allow us to access the file.
    """
    url = f"{storage_url}?restype=service&comp=userdelegationkey"
    headers = {
      'Authorization': f'Bearer {self._get_token()}',
      'x-ms-version': '2020-12-06',
      'Content-Type': 'application/xml'
    }

    # Calculate the current time (UTC) and expiry time
    current_time = datetime.now(timezone.utc) #datetime.utcnow() deprecated
    expiry_time = current_time + timedelta(hours=delegation_key_valid_hours)
    start_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    expiry_time_str = expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = f"""<?xml version="1.0" encoding="utf-8"?><KeyInfo><Start>{start_time_str}</Start><Expiry>{expiry_time_str}</Expiry></KeyInfo>"""
    response = requests.post(url, headers=headers, data=payload)

    # Extract values from the XML
    root = ET.fromstring(response.text)   
    user_delegation_key_components = {
        'SignedOid': root.find('SignedOid').text,
        'SignedTid': root.find('SignedTid').text,
        'SignedStart': root.find('SignedStart').text,
        'SignedExpiry': root.find('SignedExpiry').text,
        'SignedService': root.find('SignedService').text,
        'SignedVersion': root.find('SignedVersion').text,
        'Value': root.find('Value').text,
    }

    #Get the actual SAS token that will allow us to access the file
    sas_token = userDelegatedSasToken(user_delegation_key_components, storage_url, container_name, prefix, file_name)
    sas_token = sas_token.generate_token()
    
    return sas_token