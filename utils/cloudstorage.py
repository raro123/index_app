import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import json
from io import BytesIO
from pathlib import Path
from typing import Dict

DEFAULT_CONFIG_PATH = './config.json'
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'

class CloudflareR2:
    def __init__(self, config_path=None):
        """
        Initialize the CloudflareR2 client.
        :param config_path: Path to the config file. If None, will try to use environment variables first.
        """
        try:
            self.load_config_from_env()
        except Exception as e:
            if config_path is None:
                    config_path = DEFAULT_CONFIG_PATH
            try:
                self.load_config_from_file(config_path)
            except Exception as file_e:
                raise Exception(f"Failed to load config from environment: {e}. Failed to load config from file: {file_e}")

        self.s3_client = self.create_s3_client()

    def load_config_from_file(self, config_path):
        """Load configuration from a JSON file."""
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            self.account_id = config['account_id']
            self.access_key_id = config['access_key_id']
            self.access_key_secret = config['access_key_secret']

    def load_config_from_env(self):
        """Load configuration from environment variables (GitHub secrets)."""
        self.account_id = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
        self.access_key_id = os.environ.get('CLOUDFLARE_ACCESS_KEY_ID')
        self.access_key_secret = os.environ.get('CLOUDFLARE_ACCESS_KEY_SECRET')

        if not all([self.account_id, self.access_key_id, self.access_key_secret]):
            raise ValueError("Missing required environment variables")

    def create_s3_client(self):
        """Create and return an S3 client configured for Cloudflare R2."""
        endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret,
            region_name="auto",
            config=Config(s3={'addressing_style': 'virtual'})
        )

    def bucket_exists(self, bucket_name):
        """Check if a bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def create_bucket(self, bucket_name):
        """Create a new bucket."""
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' created successfully.")
        except ClientError as e:
            raise Exception(f"Failed to create bucket: {str(e)}")

    def ensure_bucket_exists(self, bucket_name):
        """Ensure that the specified bucket exists, creating it if necessary."""
        if not self.bucket_exists(bucket_name):
            self.create_bucket(bucket_name)

    def read_file(self, bucket_name, file_path):
        """
        Read a file from Cloudflare R2 storage.
        :param bucket_name: Name of the R2 bucket
        :param file_path: Path of the file to read (including "folders")
        :return: File content as bytes
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_path)
            return BytesIO(response['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            elif e.response['Error']['Code'] == 'NoSuchKey':
                raise Exception(f"File '{file_path}' does not exist in bucket '{bucket_name}'")
            else:
                raise Exception(f"Failed to read file: {str(e)}")

    def write_file(self, bucket_name, file_path, content, create_bucket=True):
        """
        Write a file to Cloudflare R2 storage.
        :param bucket_name: Name of the R2 bucket
        :param file_path: Path of the file to write (including "folders")
        :param content: Content to write (bytes or file-like object)
        :param create_bucket: If True, create the bucket if it doesn't exist
        """
        try:
            if create_bucket:
                self.ensure_bucket_exists(bucket_name)
            self.s3_client.put_object(Bucket=bucket_name, Key=file_path, Body=content)
            print(f"File '{file_path}' written successfully to bucket '{bucket_name}'.")
        except ClientError as e:
            raise Exception(f"Failed to write file: {str(e)}")

    def list_buckets(self):
        """
        List all buckets in the Cloudflare R2 storage.
        :return: List of bucket names
        """
        try:
            response = self.s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            return buckets
        except ClientError as e:
            raise Exception(f"Failed to list buckets: {str(e)}")

    def list_files(self, bucket_name, prefix='', delimiter='/'):
        """
        List all files (objects) in a specific bucket, optionally within a "folder".
        :param bucket_name: Name of the bucket to list files from
        :param prefix: Prefix to filter objects (simulates folder path)
        :param delimiter: Delimiter for hierarchy (default '/')
        :return: Dictionary containing files and subfolders
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                Delimiter=delimiter
            )
            
            result = {
                'files': [],
                'folders': []
            }

            if 'Contents' in response:
                # result['files'] = [{
                #     'Key': item['Key'],
                #     'Size': item['Size'],
                #     'LastModified': item['LastModified'].isoformat()
                # } for item in response['Contents'] if item['Key'] != prefix]
                result['files'] = [item['Key'] for item in response['Contents'] if item['Key'] != prefix]
            
            if 'CommonPrefixes' in response:
                result['folders'] = [prefix['Prefix'] for prefix in response['CommonPrefixes']]

            return result
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            else:
                raise Exception(f"Failed to list files in bucket '{bucket_name}': {str(e)}")

    def list_folder_contents(self, bucket_name, folder_path):
        """
        List contents of a specific "folder" in a bucket.
        :param bucket_name: Name of the bucket
        :param folder_path: Path of the folder (e.g., 'folder1/subfolder/')
        :return: Dictionary containing files and subfolders
        """
        # Ensure the folder_path ends with a '/'
        if not folder_path.endswith('/'):
            folder_path += '/'
        
        return self.list_files(bucket_name, prefix=folder_path)

# Example usage:
# if __name__ == "__main__":
#     r2_client = CloudflareR2()

#     # List all buckets
#     buckets = r2_client.list_buckets()
#     print("Available buckets:")
#     for bucket in buckets:
#         print(f"- {bucket}")

#     # Write files in different "folders"
#     r2_client.write_file('my-new-bucket', 'folder1/file1.txt', b'Hello from folder1!')
#     r2_client.write_file('my-new-bucket', 'folder1/subfolder/file2.txt', b'Hello from subfolder!')
#     r2_client.write_file('my-new-bucket', 'folder2/file3.txt', b'Hello from folder2!')

#     # List contents of the bucket root
#     contents = r2_client.list_files('my-new-bucket')
#     print("\nContents of 'my-new-bucket':")
#     for folder in contents['folders']:
#         print(f"- [Folder] {folder}")
#     for file in contents['files']:
#         print(f"- [File] {file['Key']} (Size: {file['Size']} bytes)")

#     # List contents of a specific folder
#     folder_contents = r2_client.list_folder_contents('my-new-bucket', 'folder1')
#     print("\nContents of 'folder1':")
#     for folder in folder_contents['folders']:
#         print(f"- [Folder] {folder}")
#     for file in folder_contents['files']:
#         print(f"- [File] {file['Key']} (Size: {file['Size']} bytes)")

#     # Read a file from a subfolder
#     content = r2_client.read_file('my-new-bucket', 'folder1/subfolder/file2.txt')
#     print(f"\nContent of 'folder1/subfolder/file2.txt': {content.decode('utf-8')}")


def get_storage_options() -> Dict[str, str]:
    """
    Fetch storage options from GitHub Actions environment if exists,
    otherwise from config.json.

    Returns:
        Dict[str, str]: A dictionary containing storage options.
    """
    # Check if running in GitHub Actions
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        # Fetch from environment variables
        config =  {
            'access_key_id': os.environ.get('CLOUDFLARE_ACCESS_KEY_ID', ''),
            'access_key_secret': os.environ.get('CLOUDFLARE_ACCESS_KEY_SECRET', ''),
            'account_id': os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
        }
    else:
        # Fetch from config.json
        config_path = Path(DEFAULT_CONFIG_PATH)
        if config_path.exists():
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
        else:
            return {}
    storage_options = {"aws_access_key_id": config['access_key_id'],
                        "aws_secret_access_key": config['access_key_secret'],
                        "aws_region": "auto",
                        "endpoint": f'https://{config["account_id"]}.r2.cloudflarestorage.com',
                         'AWS_S3_ALLOW_UNSAFE_RENAME': 'True'}
    return storage_options