"""
MongoDB Atlas service for document storage and analytics
"""
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    from bson import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None
    ConnectionFailure = Exception
    ServerSelectionTimeoutError = Exception
    ObjectId = str

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from app.config import settings

class MongoDBService:
    def __init__(self):
        """Initialize MongoDB Atlas connection"""
        if not PYMONGO_AVAILABLE:
            raise ImportError("pymongo not available. Install with: pip install pymongo")
            
        try:
            if not settings.MONGODB_URL:
                raise Exception("MongoDB configuration missing. Please set MONGODB_URL")
            
            # Create MongoDB client
            self.client = MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            
            # Get database
            self.db = self.client[settings.MONGODB_DATABASE_NAME]
            
            # Get collections
            self.documents_collection = self.db[settings.MONGODB_COLLECTION_DOCUMENTS]
            self.analytics_collection = self.db[settings.MONGODB_COLLECTION_ANALYTICS]
            self.logs_collection = self.db[settings.MONGODB_COLLECTION_LOGS]
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            raise Exception(f"Failed to initialize MongoDB service: {str(e)}")
    
    def _test_connection(self):
        """Test MongoDB connection"""
        try:
            # The ismaster command is cheap and does not require auth
            self.client.admin.command('ismaster')
            print("MongoDB Atlas connection successful")
        except ConnectionFailure:
            raise Exception("MongoDB connection failed")
        except ServerSelectionTimeoutError:
            raise Exception("MongoDB server selection timeout")
    
    def _serialize_document(self, doc: Dict) -> Dict:
        """Convert MongoDB document to JSON serializable format"""
        if doc:
            # Convert ObjectId to string
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            
            # Convert datetime objects to ISO format
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
                elif isinstance(value, ObjectId):
                    doc[key] = str(value)
        
        return doc
    
    # Document Storage Operations
    def store_document(self, document_data: Dict) -> Optional[str]:
        """Store document in MongoDB"""
        try:
            # Add timestamp
            document_data['created_at'] = datetime.utcnow()
            document_data['updated_at'] = datetime.utcnow()
            
            result = self.documents_collection.insert_one(document_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error storing document: {str(e)}")
            return None
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID from MongoDB"""
        try:
            doc = self.documents_collection.find_one({'_id': ObjectId(document_id)})
            return self._serialize_document(doc) if doc else None
            
        except Exception as e:
            print(f"Error getting document: {str(e)}")
            return None
    
    def update_document(self, document_id: str, update_data: Dict) -> bool:
        """Update document in MongoDB"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.documents_collection.update_one(
                {'_id': ObjectId(document_id)},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from MongoDB"""
        try:
            result = self.documents_collection.delete_one({'_id': ObjectId(document_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
    
    def search_documents(self, user_id: str, query: str, filters: Optional[Dict] = None, limit: int = 50) -> List[Dict]:
        """Search documents with full-text search"""
        try:
            # Build search query
            search_filter: Dict[str, Any] = {'user_id': user_id}
            
            # Add text search if query provided
            if query:
                search_filter['$text'] = {'$search': query}
            
            # Add additional filters
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        search_filter[key] = value
            
            # Execute search
            cursor = self.documents_collection.find(search_filter).limit(limit)
            
            # Convert results
            results = []
            for doc in cursor:
                results.append(self._serialize_document(doc))
            
            return results
            
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []
    
    def get_user_documents(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict]:
        """Get user documents with pagination"""
        try:
            cursor = self.documents_collection.find({'user_id': user_id})\
                .sort('created_at', -1)\
                .skip(skip)\
                .limit(limit)
            
            results = []
            for doc in cursor:
                results.append(self._serialize_document(doc))
            
            return results
            
        except Exception as e:
            print(f"Error getting user documents: {str(e)}")
            return []
    
    # Analytics Operations
    def store_analytics_event(self, event_data: Dict) -> Optional[str]:
        """Store analytics event"""
        try:
            event_data['timestamp'] = datetime.utcnow()
            result = self.analytics_collection.insert_one(event_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error storing analytics event: {str(e)}")
            return None
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> Dict:
        """Get user analytics for specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Document count
            doc_count = self.documents_collection.count_documents({'user_id': user_id})
            
            # Recent documents
            recent_docs = self.documents_collection.count_documents({
                'user_id': user_id,
                'created_at': {'$gte': start_date}
            })
            
            # Document categories
            category_pipeline = [
                {'$match': {'user_id': user_id}},
                {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            
            categories = list(self.documents_collection.aggregate(category_pipeline))
            
            # Activity events
            activity_pipeline = [
                {'$match': {
                    'user_id': user_id,
                    'timestamp': {'$gte': start_date}
                }},
                {'$group': {'_id': '$event_type', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            
            activities = list(self.analytics_collection.aggregate(activity_pipeline))
            
            return {
                'total_documents': doc_count,
                'recent_documents': recent_docs,
                'categories': [self._serialize_document(cat) for cat in categories],
                'activities': [self._serialize_document(act) for act in activities],
                'period_days': days
            }
            
        except Exception as e:
            print(f"Error getting user analytics: {str(e)}")
            return {}
    
    def get_system_analytics(self, days: int = 7) -> Dict:
        """Get system-wide analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total documents
            total_docs = self.documents_collection.count_documents({})
            
            # Recent uploads
            recent_uploads = self.documents_collection.count_documents({
                'created_at': {'$gte': start_date}
            })
            
            # Top categories
            category_pipeline = [
                {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            
            top_categories = list(self.documents_collection.aggregate(category_pipeline))
            
            # User activity
            user_activity_pipeline = [
                {'$match': {'timestamp': {'$gte': start_date}}},
                {'$group': {'_id': '$user_id', 'event_count': {'$sum': 1}}},
                {'$sort': {'event_count': -1}},
                {'$limit': 10}
            ]
            
            active_users = list(self.analytics_collection.aggregate(user_activity_pipeline))
            
            return {
                'total_documents': total_docs,
                'recent_uploads': recent_uploads,
                'top_categories': [self._serialize_document(cat) for cat in top_categories],
                'active_users': [self._serialize_document(user) for user in active_users],
                'period_days': days
            }
            
        except Exception as e:
            print(f"Error getting system analytics: {str(e)}")
            return {}
    
    # Logging Operations
    def log_event(self, log_data: Dict) -> Optional[str]:
        """Log event to MongoDB"""
        try:
            log_data['timestamp'] = datetime.utcnow()
            result = self.logs_collection.insert_one(log_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error logging event: {str(e)}")
            return None
    
    def get_logs(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Get logs with optional filters"""
        try:
            query = filters or {}
            
            cursor = self.logs_collection.find(query)\
                .sort('timestamp', -1)\
                .limit(limit)
            
            results = []
            for log in cursor:
                results.append(self._serialize_document(log))
            
            return results
            
        except Exception as e:
            print(f"Error getting logs: {str(e)}")
            return []
    
    # Aggregation Operations
    def get_document_trends(self, user_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Get document upload trends"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            match_stage: Dict[str, Any] = {'created_at': {'$gte': start_date}}
            if user_id:
                match_stage['user_id'] = user_id
            
            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$created_at'},
                        'month': {'$month': '$created_at'},
                        'day': {'$dayOfMonth': '$created_at'}
                    },
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            results = list(self.documents_collection.aggregate(pipeline))
            return [self._serialize_document(result) for result in results]
            
        except Exception as e:
            print(f"Error getting document trends: {str(e)}")
            return []
    
    # Backup and Maintenance
    def create_backup_index(self) -> bool:
        """Create backup indexes for better performance"""
        try:
            # Create indexes
            self.documents_collection.create_index([('user_id', 1), ('created_at', -1)])
            self.documents_collection.create_index([('user_id', 1), ('category', 1)])
            self.documents_collection.create_index([('$**', 'text')])  # Text search index
            
            self.analytics_collection.create_index([('user_id', 1), ('timestamp', -1)])
            self.analytics_collection.create_index([('event_type', 1)])
            
            self.logs_collection.create_index([('timestamp', -1)])
            self.logs_collection.create_index([('level', 1)])
            
            return True
            
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics for all collections"""
        try:
            docs_stats = self.db.command('collStats', settings.MONGODB_COLLECTION_DOCUMENTS)
            analytics_stats = self.db.command('collStats', settings.MONGODB_COLLECTION_ANALYTICS)
            logs_stats = self.db.command('collStats', settings.MONGODB_COLLECTION_LOGS)
            
            return {
                'documents': {
                    'count': docs_stats.get('count', 0),
                    'size': docs_stats.get('size', 0),
                    'avg_obj_size': docs_stats.get('avgObjSize', 0)
                },
                'analytics': {
                    'count': analytics_stats.get('count', 0),
                    'size': analytics_stats.get('size', 0),
                    'avg_obj_size': analytics_stats.get('avgObjSize', 0)
                },
                'logs': {
                    'count': logs_stats.get('count', 0),
                    'size': logs_stats.get('size', 0),
                    'avg_obj_size': logs_stats.get('avgObjSize', 0)
                }
            }
            
        except Exception as e:
            print(f"Error getting collection stats: {str(e)}")
            return {}
    
    def health_check(self) -> Dict:
        """Check MongoDB service health"""
        try:
            # Test database connection
            result = self.client.admin.command('ping')
            
            return {
                'status': 'healthy',
                'database_accessible': result.get('ok') == 1,
                'timestamp': datetime.utcnow().isoformat(),
                'database_name': settings.MONGODB_DATABASE_NAME
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database_accessible': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'database_name': settings.MONGODB_DATABASE_NAME
            }
    
    def close_connection(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing MongoDB connection: {str(e)}")

# Create global instance lazily
mongodb_service = None

def get_mongodb_service():
    global mongodb_service
    if mongodb_service is None:
        mongodb_service = MongoDBService()
    return mongodb_service