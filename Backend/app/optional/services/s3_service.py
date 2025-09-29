"""
AWS S3 service for file storage and management
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, List, BinaryIO
import uuid
from datetime import datetime, timedelta
import mimetypes
import os
from urllib.parse import urlparse

from app.config import settings

class S3Service:
    def __init__(self):
        """Initialize S3 service with AWS credentials"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.AWS_S3_BUCKET_NAME
            self.use_ssl = settings.AWS_S3_USE_SSL
            
            # Test connection
            self._test_connection()
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        except Exception as e:
            raise Exception(f"Failed to initialize S3 service: {str(e)}")
    
    def _test_connection(self):
        """Test S3 connection and bucket access"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise Exception(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise Exception(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise Exception(f"Error accessing S3 bucket: {str(e)}")
    
    def upload_file(
        self, 
        file_obj: BinaryIO, 
        filename: str, 
        folder: str = None,
        content_type: str = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Upload file to S3 bucket
        
        Args:
            file_obj: File object to upload
            filename: Name of the file
            folder: S3 folder/prefix (optional)
            content_type: MIME type of the file (optional)
            metadata: Additional metadata (optional)
        
        Returns:
            Dict containing upload information
        """
        try:
            # Generate unique file key
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1]
            
            # Construct S3 key
            if folder:
                s3_key = f"{folder}/{file_id}{file_extension}"
            else:
                s3_key = f"{settings.S3_UPLOAD_FOLDER}/{file_id}{file_extension}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_obj,
                'ContentType': content_type,
            }
            
            # Add metadata if provided
            if metadata:
                upload_params['Metadata'] = {
                    'original_filename': filename,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    **metadata
                }
            else:
                upload_params['Metadata'] = {
                    'original_filename': filename,
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            
            # Upload file
            self.s3_client.upload_fileobj(**upload_params)
            
            # Generate file URL
            file_url = self.get_file_url(s3_key)
            
            return {
                'success': True,
                'file_id': file_id,
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'url': file_url,
                'content_type': content_type,
                'original_filename': filename,
                'upload_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    def download_file(self, s3_key: str) -> Optional[bytes]:
        """
        Download file from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            File content as bytes or None if error
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Error downloading file {s3_key}: {str(e)}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            print(f"Error deleting file {s3_key}: {str(e)}")
            return False
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for file access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL
        """
        try:
            if settings.AWS_S3_CUSTOM_DOMAIN:
                # Use custom domain (e.g., CloudFront)
                protocol = "https" if self.use_ssl else "http"
                return f"{protocol}://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
            else:
                # Generate presigned URL
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
                return url
        except Exception as e:
            print(f"Error generating URL for {s3_key}: {str(e)}")
            return ""
    
    def list_files(self, prefix: str = "", max_keys: int = 100) -> List[Dict]:
        """
        List files in S3 bucket
        
        Args:
            prefix: S3 key prefix to filter by
            max_keys: Maximum number of files to return
        
        Returns:
            List of file information dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"'),
                        'url': self.get_file_url(obj['Key'])
                    })
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def move_file(self, source_key: str, destination_key: str) -> bool:
        """
        Move file within S3 bucket
        
        Args:
            source_key: Current S3 key
            destination_key: New S3 key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Copy file to new location
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_key
            )
            
            # Delete original file
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=source_key)
            
            return True
            
        except Exception as e:
            print(f"Error moving file from {source_key} to {destination_key}: {str(e)}")
            return False
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict]:
        """
        Get file metadata from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Metadata dictionary or None if error
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'content_type': response.get('ContentType', ''),
                'content_length': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified', '').isoformat() if response.get('LastModified') else '',
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            print(f"Error getting metadata for {s3_key}: {str(e)}")
            return None
    
    def create_backup(self, s3_key: str) -> Optional[str]:
        """
        Create backup copy of file
        
        Args:
            s3_key: S3 object key to backup
        
        Returns:
            Backup S3 key or None if error
        """
        try:
            # Generate backup key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(s3_key)
            backup_key = f"{settings.S3_BACKUP_FOLDER}/{timestamp}_{filename}"
            
            # Copy file to backup location
            copy_source = {'Bucket': self.bucket_name, 'Key': s3_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=backup_key,
                MetadataDirective='COPY'
            )
            
            return backup_key
            
        except Exception as e:
            print(f"Error creating backup for {s3_key}: {str(e)}")
            return None
    
    def get_bucket_info(self) -> Dict:
        """
        Get S3 bucket information and statistics
        
        Returns:
            Bucket information dictionary
        """
        try:
            # Get bucket location
            location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            
            # Get bucket size (approximate)
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            total_size = 0
            file_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    total_size += obj['Size']
                    file_count += 1
            
            return {
                'bucket_name': self.bucket_name,
                'region': location.get('LocationConstraint', 'us-east-1'),
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'bucket_name': self.bucket_name
            }

# Create global instance lazily
s3_service = None

def get_s3_service():
    global s3_service
    if s3_service is None:
        s3_service = S3Service()
    return s3_service