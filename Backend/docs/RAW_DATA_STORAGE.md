# Raw Data Storage System Documentation

## Overview

The Raw Data Storage System provides specialized AWS S3 storage for raw data from various sources including emails, documents, IoT devices, and analytics. It extends the basic S3Service with advanced features like compression, metadata enrichment, and hierarchical organization.

## Key Features

### 1. Data Compression and Optimization
- **Gzip Compression**: All data is compressed using gzip to reduce storage costs
- **Checksum Validation**: MD5 checksums ensure data integrity
- **Storage Class Optimization**: Uses AWS S3 Standard-IA for cost-effective storage

### 2. Hierarchical Organization
```
{S3_RAW_DATA_FOLDER}/
├── email/
│   ├── {user_id}/
│   │   └── {year}/{month}/{day}/
│   │       └── email_{timestamp}_{hash}.json.gz
├── document/
│   ├── {user_id}/
│   │   └── {year}/{month}/{day}/
│   │       ├── doc_{timestamp}_{hash}.json.gz
│   │       └── file_{timestamp}_{filename}
├── iot/
│   ├── {device_id}/
│   │   └── {year}/{month}/{day}/
│   │       └── iot_{timestamp}_{hash}.json.gz
└── analytics/
    ├── {user_id}/
    │   └── {year}/{month}/{day}/
    │       └── analytics_{timestamp}_{source}.json.gz
```

### 3. Metadata Enrichment
Each stored object includes comprehensive metadata:
- User ID and device information
- Data source and type classification
- Processing timestamps
- Data size and compression ratio
- Custom tags for categorization

## Configuration

### Environment Variables
```bash
# Raw Data Storage Configuration
S3_RAW_DATA_FOLDER=raw-data
S3_RAW_EMAIL_FOLDER=raw-data/email
S3_RAW_DOCUMENT_FOLDER=raw-data/document
S3_RAW_IOT_FOLDER=raw-data/iot
S3_RAW_ANALYTICS_FOLDER=raw-data/analytics

# Retention and Lifecycle
RAW_DATA_RETENTION_DAYS=365
RAW_DATA_STORAGE_CLASS=STANDARD_IA
RAW_DATA_ARCHIVE_DAYS=90
```

### AWS S3 Settings
- **Region**: ap-south-1 (Mumbai)
- **Storage Class**: STANDARD_IA (cost-optimized)
- **Lifecycle Rules**: Automatic archival after 90 days
- **Retention**: 365 days default retention

## API Endpoints

### Raw Data Storage Endpoints (`/api/raw-data/`)

#### Store Raw Email Data
```http
POST /api/raw-data/email/store
Content-Type: application/json

{
    "id": "email_id",
    "subject": "Email Subject",
    "from": "sender@example.com",
    "body": "Email content...",
    "headers": {...},
    "attachments": [...]
}
```

#### Store Raw Document Data
```http
POST /api/raw-data/document/store
Content-Type: multipart/form-data

{
    "document_data": {
        "title": "Document Title",
        "type": "invoice",
        "metadata": {...}
    },
    "file": <file_upload>
}
```

#### Store Raw IoT Data
```http
POST /api/raw-data/iot/store
Content-Type: application/json

{
    "sensor_data": {
        "temperature": 25.5,
        "humidity": 60,
        "timestamp": "2024-01-15T10:30:00Z"
    },
    "device_id": "sensor_001"
}
```

#### Store Raw Analytics Data
```http
POST /api/raw-data/analytics/store
Content-Type: application/json

{
    "event_type": "user_action",
    "action": "document_upload",
    "user_id": "123",
    "metadata": {...}
}
```

#### Retrieve Raw Data
```http
GET /api/raw-data/retrieve/{s3_key}
```

#### List Raw Data Files
```http
GET /api/raw-data/list?data_type=email&days=30&limit=100
```

#### Batch Store Raw Data
```http
POST /api/raw-data/batch-store
Content-Type: application/json

{
    "data_items": [...],
    "data_type": "email"
}
```

### Email Integration Endpoints (`/api/email/`)

#### Fetch Emails with Raw Storage
```http
GET /api/email/fetch-with-raw-storage?hours=24&process_documents=true
```

#### Fetch Emails with Optional Raw Storage
```http
GET /api/email/fetch?hours=24&store_raw=true&process_documents=true
```

## Service Integration

### Email Service Integration
```python
# Automatically store raw email data
email_service = EmailService(db)
emails = email_service.fetch_recent_emails(
    hours=24, 
    store_raw=True, 
    user_id=user_id
)
```

### Document Service Integration
```python
# Store raw document data with file content
raw_data_service = RawDataStorageService()
result = raw_data_service.store_raw_document_data(
    document_data, 
    user_id, 
    file_content
)
```

### IoT Service Integration
```python
# Store raw IoT sensor data
raw_data_service = RawDataStorageService()
result = raw_data_service.store_raw_iot_data(
    sensor_data, 
    device_id, 
    user_id
)
```

## Administrative Features

### Data Cleanup (Admin Only)
```http
POST /api/raw-data/cleanup?force=true
```

### Data Archival (Admin Only)
```http
POST /api/raw-data/archive?days_old=90&force=true
```

### Statistics (Admin Only)
```http
GET /api/raw-data/statistics
```

### Health Check
```http
GET /api/raw-data/health
```

## Data Retention and Lifecycle

### Automatic Lifecycle Management
1. **Standard-IA Storage**: All new data stored in Standard-IA class
2. **Archival**: Data older than 90 days moved to Glacier
3. **Deletion**: Data older than 365 days automatically deleted
4. **Cleanup Jobs**: Background tasks for maintenance

### Manual Management
- Admin users can trigger cleanup and archival manually
- Force immediate processing for maintenance
- Statistics and monitoring for storage usage

## Security and Access Control

### Authentication
- JWT token-based authentication required
- User-specific data access controls
- Admin privileges for management operations

### Data Privacy
- User data isolated by user_id
- Non-admin users can only access their own data
- Encrypted storage in AWS S3

### Permissions
- **Users**: Store and retrieve own data
- **Admins**: Full access, cleanup, statistics, archival

## Performance Considerations

### Storage Optimization
- Gzip compression reduces storage by ~70%
- Hierarchical folder structure for efficient queries
- Standard-IA class reduces costs by ~40%

### API Efficiency
- Background processing for batch operations
- Streaming uploads for large files
- Pagination for list operations

### Monitoring
- Health check endpoints
- Storage statistics and usage metrics
- Error tracking and logging

## Error Handling

### Common Error Scenarios
1. **AWS Connection Issues**: Fallback and retry logic
2. **Storage Quota Exceeded**: Automatic cleanup triggers
3. **Invalid Data Format**: Validation and sanitization
4. **Authentication Failures**: Proper error responses

### Error Responses
```json
{
    "error": "Error description",
    "code": "ERROR_CODE",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "unique_id"
}
```

## Usage Examples

### Basic Email Data Storage
```python
# Fetch and store raw email data
emails = email_service.fetch_recent_emails(
    hours=24, 
    store_raw=True, 
    user_id="user123"
)

# Each email object will include raw_storage info
for email in emails:
    if email.get('raw_storage', {}).get('success'):
        print(f"Stored: {email['raw_storage']['s3_key']}")
```

### Document Processing with Raw Storage
```python
# Process document and store raw data
document_data = {
    "title": "Invoice #12345",
    "type": "invoice",
    "date": "2024-01-15"
}

result = raw_data_service.store_raw_document_data(
    document_data, 
    user_id, 
    file_content
)
```

### IoT Data Collection
```python
# Store IoT sensor readings
sensor_data = {
    "temperature": 25.5,
    "humidity": 60,
    "location": "warehouse_a",
    "timestamp": datetime.now().isoformat()
}

result = raw_data_service.store_raw_iot_data(
    sensor_data, 
    "sensor_001", 
    user_id
)
```

## Best Practices

### Data Organization
1. Use consistent naming conventions
2. Include comprehensive metadata
3. Organize by user and date hierarchy
4. Tag data for easy categorization

### Performance
1. Use batch operations for multiple items
2. Enable compression for all data
3. Monitor storage usage regularly
4. Implement proper error handling

### Security
1. Validate all input data
2. Use proper authentication
3. Implement access controls
4. Monitor for suspicious activity

### Cost Optimization
1. Use appropriate storage classes
2. Implement lifecycle policies
3. Regular cleanup of old data
4. Monitor and optimize usage patterns

## Troubleshooting

### Common Issues
1. **Storage Failures**: Check AWS credentials and permissions
2. **Large Files**: Use multipart upload for files >100MB
3. **High Costs**: Review lifecycle policies and cleanup frequency
4. **Slow Performance**: Check network connectivity and region settings

### Monitoring Commands
```bash
# Check service health
curl -X GET "/api/raw-data/health"

# View storage statistics (admin)
curl -X GET "/api/raw-data/statistics"

# List recent data
curl -X GET "/api/raw-data/list?days=7"
```

This documentation provides comprehensive guidance for using the Raw Data Storage System effectively and securely.