import boto3
from botocore.config import Config
from backend.core.config import get_settings

class R2Storage:
    def __init__(self):
        settings = get_settings()
        self.bucket_name = settings.R2_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            endpoint_url = (
                f"https://{settings.R2_ACCOUNT_ID}"
                ".r2.cloudflarestorage.com"
            ),
            aws_access_key_id = settings.R2_ACCESS_KEY_ID.get_secret_value(),
            aws_secret_access_key = settings.R2_SECRET_ACCESS_KEY.get_secret_value(),
            region_name = "auto",
            config = Config(
                signature_version = "s3v4"
            ),
        )
    def upload_file(
            self,
            file,
            object_key : str,
            content_type : str | None = None,
    ) -> None :
        extra_args={}

        if content_type:
            extra_args["ContentType"] = content_type    

        self.client.upload_fileobj(
            file,
            self.bucket_name,
            object_key,
            ExtraArgs = extra_args
        ) 

    def delete_file(
            self,
            object_key : str
    )-> None:
        self.client.delete_object(
            Bucket = self.bucket_name,
            Key = object_key,
        )
_r2_storage : R2Storage | None = None

def get_r2_storage() -> R2Storage:
    global _r2_storage
    if _r2_storage is None:
        _r2_storage = R2Storage()
    return _r2_storage
        
