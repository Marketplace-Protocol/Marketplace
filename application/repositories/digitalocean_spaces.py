
from boto3 import client

from application.errors import S3Error
from application.settings import DIGITALOCEAN_SPACES_REGION, DIGITALOCEAN_SPACES_ENDPOINT, \
    DIGITALOCEAN_SPACES_ACCESS_KEY_ID, DIGITALOCEAN_SPACES_ACCESS_KEY_SECRET_KEY

from loguru import logger


class DigitalOceanSpaces:
    def __init__(self) -> None:
        self.s3_client = client(
            's3',
            region_name=DIGITALOCEAN_SPACES_REGION,
            endpoint_url=DIGITALOCEAN_SPACES_ENDPOINT,
            aws_access_key_id=DIGITALOCEAN_SPACES_ACCESS_KEY_ID,
            aws_secret_access_key=DIGITALOCEAN_SPACES_ACCESS_KEY_SECRET_KEY
        )

    def read_privatEdit_file(self, file_key: str) -> None:
        try:
            self.s3_client.download_file(
                Bucket='privatedit',
                Key=file_key,
                Filename=file_key
            )
            return
        except Exception as e:
            logger.info("DigitalOcean spaces error", kv={
                'action': 'download',
                'file_key': file_key,
                'error_details': str(e),
            })
            raise S3Error(
                action='download',
                retryable=False,
                message=str(e)
            )

    def write_privatEdit_file(self, file_key: str) -> None:
        try:
            self.s3_client.upload_file(
                Bucket='privatedit',
                Key=file_key,
                Filename=file_key
            )
            return
        except Exception as e:
            logger.info("DigitalOcean spaces error", kv={
                'action': 'upload',
                'file_key': file_key,
                'error_details': str(e),
            })
            raise S3Error(
                action='upload',
                retryable=False,
                message=str(e)
            )

    def generate_pre_signed_url(self, file_key: str) -> str:
        try:
            # Generate the pre-signed URL
            url = self.s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={'Bucket': 'privatedit', 'Key': file_key, 'ACL': 'private'},
                ExpiresIn=900  # URL expires in 15 minutes
            )

            return url

        except Exception as e:
            logger.info("DigitalOcean spaces error", kv={
                'action': 'pre-sign',
                'file_key': file_key,
                'error_details': str(e),
            })
            raise S3Error(
                action='pre-sign',
                retryable=False,
                message=str(e)
            )
