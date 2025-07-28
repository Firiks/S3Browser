import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Optional, Tuple
import os


class S3Client:
    """Common S3 client for handling connections and operations."""
    
    def __init__(self, access_key: str = None, secret_key: str = None, 
                 region: str = None, endpoint_url: str = None):
        """
        Initialize S3 client with credentials.
        
        Args:
            access_key: AWS access key or S3-compatible access key
            secret_key: AWS secret key or S3-compatible secret key
            region: AWS region or S3-compatible region
            endpoint_url: Custom endpoint URL for S3-compatible services
        """
        self.access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.endpoint_url = endpoint_url or os.getenv('S3_ENDPOINT_URL')
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to S3 service."""
        try:
            session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            if self.endpoint_url:
                self.client = session.client('s3', endpoint_url=self.endpoint_url)
            else:
                self.client = session.client('s3')
                
        except NoCredentialsError:
            raise Exception("No credentials provided. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or pass them as parameters.")
        except Exception as e:
            raise Exception(f"Failed to connect to S3: {str(e)}")
    
    def list_buckets(self) -> List[Dict]:
        """List all available buckets."""
        try:
            response = self.client.list_buckets()
            return [
                {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate']
                }
                for bucket in response['Buckets']
            ]
        except ClientError as e:
            raise Exception(f"Failed to list buckets: {str(e)}")
    
    def list_objects(self, bucket_name: str, prefix: str = '', delimiter: str = '/', max_keys: int = 1000, continuation_token: str = None,
                    key_substring: str = None, min_size: int = None, max_size: int = None,
                    modified_after: str = None, modified_before: str = None,
                    sort_by: str = None, sort_order: str = 'asc') -> Tuple[List[Dict], List[str], Optional[str]]:
        """
        List objects and prefixes in a bucket with pagination, search, filter, and sorting support.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Prefix to filter objects (S3 native)
            delimiter: Delimiter for common prefixes
            max_keys: Maximum number of keys to return (default: 1000)
            continuation_token: Token for paginated results
            key_substring: Substring to search for in object keys (case-insensitive)
            min_size: Minimum object size in bytes
            max_size: Maximum object size in bytes
            modified_after: Only include objects modified after this ISO date string (e.g. '2023-01-01T00:00:00Z')
            modified_before: Only include objects modified before this ISO date string
            sort_by: Field to sort by ('key', 'size', 'last_modified')
            sort_order: 'asc' or 'desc'
            
        Returns:
            Tuple of (objects, prefixes, next_continuation_token)
        
        Note:
            S3 only supports prefix filtering natively. All other filters and sorting are applied in Python
            after fetching the page of results. This means filtering is limited to the objects returned in the current page.
        """
        # Manual pagination is used here for UI-friendly next/prev navigation.
        # For batch processing or iterating all objects, consider using:
        # paginator = self.client.get_paginator('list_objects_v2')
        # for page in paginator.paginate(...): ...
        import dateutil.parser
        try:
            params = {
                'Bucket': bucket_name,
                'Prefix': prefix,
                'Delimiter': delimiter,
                'MaxKeys': max_keys
            }
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            response = self.client.list_objects_v2(**params)
            
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })
            
            # Filtering
            if key_substring:
                objects = [o for o in objects if key_substring.lower() in o['key'].lower()]
            if min_size is not None:
                objects = [o for o in objects if o['size'] >= min_size]
            if max_size is not None:
                objects = [o for o in objects if o['size'] <= max_size]
            if modified_after:
                after_dt = dateutil.parser.isoparse(modified_after)
                objects = [o for o in objects if o['last_modified'] >= after_dt]
            if modified_before:
                before_dt = dateutil.parser.isoparse(modified_before)
                objects = [o for o in objects if o['last_modified'] <= before_dt]
            
            # Sorting
            if sort_by in {'key', 'size', 'last_modified'}:
                reverse = (sort_order == 'desc')
                objects = sorted(objects, key=lambda o: o[sort_by], reverse=reverse)
            
            prefixes = []
            if 'CommonPrefixes' in response:
                for prefix_obj in response['CommonPrefixes']:
                    prefixes.append(prefix_obj['Prefix'])
            
            next_token = response.get('NextContinuationToken') if response.get('IsTruncated') else None
            
            return objects, prefixes, next_token
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            else:
                raise Exception(f"Failed to list objects: {str(e)}")
    
    def get_object_info(self, bucket_name: str, key: str) -> Dict:
        """Get detailed information about a specific object, including MIME type."""
        import mimetypes
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=key)
            content_type = response.get('ContentType', '')
            # Fallback to mimetypes if ContentType is missing or generic
            if not content_type or content_type == 'binary/octet-stream':
                guessed, _ = mimetypes.guess_type(key)
                content_type = guessed or content_type or 'application/octet-stream'
            return {
                'key': key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'],
                'content_type': response.get('ContentType', ''),
                'mime_type': content_type,
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise Exception(f"Object '{key}' does not exist in bucket '{bucket_name}'")
            else:
                raise Exception(f"Failed to get object info: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test if the S3 connection is working."""
        try:
            self.client.list_buckets()
            return True
        except Exception:
            return False 