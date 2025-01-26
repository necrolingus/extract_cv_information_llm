import hmac
import hashlib
import base64
from urllib.parse import quote


class userDelegatedSasToken:
    def __init__(self, user_delegation_key_components, storage_url, container_name, prefix, file_name):
        self.signed_oid = user_delegation_key_components["SignedOid"]
        self.signed_tid = user_delegation_key_components["SignedTid"]
        self.signed_key_start = user_delegation_key_components["SignedStart"]
        self.signed_key_expiry = user_delegation_key_components["SignedExpiry"]
        self.signed_service = user_delegation_key_components["SignedService"]
        self.signed_version = user_delegation_key_components["SignedVersion"]
        self.signed_key = user_delegation_key_components["Value"]
        self.storage_url = storage_url
        self.container_name = container_name
        self.prefix = prefix
        self.file_name = file_name

        #static variables
        self.permissions = "r" #rl for read and list
        self.signed_key_service = "b" #Currently, only Blob Storage is supported, always use b (sks)
        self.signed_storage_version = "2020-12-06"
        self.signed_protocol = "https"
        self.signed_resource = "b" #use c for container and b for blob (sr)

        #SAS url valid from and expiry
        #just reuse the start and end times of the user delgation key for this. There is no reason
        #to make expiration any longer or shorter than the value the user passes through e.g. 1 hour
        self.signed_start = self.signed_key_start
        self.signed_expiry = self.signed_key_expiry


    def generate_token(self):
        #Get the container name only and build the canonical resource
        storage_account_name_only = self.storage_url.split('https://')[1].split('.')[0]
        canonical_resource = f"/blob/{storage_account_name_only}/{self.container_name}/{self.prefix}/{self.file_name}"

        # Canonical string with all necessary fields
        canonical_string = (
            f"{self.permissions}\n"  # Permissions
            f"{self.signed_start}\n"  # Start time
            f"{self.signed_expiry}\n"  # Expiry time
            f"{canonical_resource}\n"  # Decoded canonicalized resource
            f"{self.signed_oid}\n"  # Signed Object ID
            f"{self.signed_tid}\n"  # Signed Tenant ID
            f"{self.signed_key_start}\n"  # Start time of user delegation key
            f"{self.signed_key_expiry}\n"  # Expiry time of user delegation key
            f"{self.signed_key_service}\n"  # Signed service
            f"{self.signed_version}\n"  # Signed key version
            "\n"  # Signed authorized user object ID (optional, blank here)
            "\n"  # Signed unauthorized user object ID (optional, blank here)
            "\n"  # Signed correlation ID (optional, blank here)
            "\n"  # Signed IP (optional, blank here)
            f"{self.signed_protocol}\n"  # Signed protocol
            f"{self.signed_storage_version}\n"  # Storage version (sv)
            f"{self.signed_resource}\n"  # Signed resource (sr)
            "\n"
            "\n"
            "\n"
            "\n"
            "\n"
            "\n"
            ""
        )

        #Sign the canonical string with our user delegation key
        key = base64.b64decode(self.signed_key)
        signature = hmac.new(key, canonical_string.encode('utf-8'), hashlib.sha256).digest()
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        encoded_signature = quote(signature_b64, safe="")

        #Generate the SAS token
        sas_token = (
                    f"{self.storage_url}{self.container_name}/{self.prefix}/{self.file_name}"
                    f"?sp={self.permissions}"
                    f"&st={self.signed_start}"
                    f"&se={self.signed_expiry}"
                    f"&skoid={self.signed_oid}"
                    f"&sktid={self.signed_tid}"
                    f"&skt={self.signed_key_start}"
                    f"&ske={self.signed_key_expiry}"
                    f"&sks={self.signed_key_service}"
                    f"&skv={self.signed_version}"
                    f"&spr={self.signed_protocol}"
                    f"&sv={self.signed_storage_version}"
                    f"&sr={self.signed_resource}"
                    f"&sig={encoded_signature}"
                )

        return sas_token