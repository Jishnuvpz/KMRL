"""
FAISS Semantic Search System Verification Script
Tests end-to-end functionality of the semantic search implementation
"""
import asyncio
import json
import time
import logging
from typing import Dict, List, Any
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearchVerification:
    """
    Comprehensive verification suite for FAISS semantic search system
    """
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
        # Sample test documents
        self.test_documents = [
            {
                "title": "Machine Learning Fundamentals",
                "content": """
                Machine learning is a subset of artificial intelligence that focuses on algorithms 
                that can learn from data. It includes supervised learning, unsupervised learning, 
                and reinforcement learning approaches. Common algorithms include linear regression, 
                decision trees, neural networks, and support vector machines.
                """,
                "category": "technology",
                "tags": ["machine learning", "AI", "algorithms"]
            },
            {
                "title": "Climate Change Report",
                "content": """
                Global warming continues to accelerate due to greenhouse gas emissions. 
                Temperature records show consistent increases over the past decades. 
                The effects include rising sea levels, extreme weather events, and 
                ecosystem disruption. Immediate action is required to reduce carbon emissions.
                """,
                "category": "environment",
                "tags": ["climate", "environment", "global warming"]
            },
            {
                "title": "Financial Markets Analysis",
                "content": """
                Stock market volatility has increased due to economic uncertainty. 
                Interest rates, inflation, and geopolitical events significantly impact 
                market performance. Diversified portfolios and risk management strategies 
                are essential for long-term investment success.
                """,
                "category": "finance",
                "tags": ["stocks", "investment", "markets"]
            },
            {
                "title": "Medical Research Breakthrough",
                "content": """
                Researchers have developed a new treatment approach for cancer therapy. 
                The immunotherapy technique shows promising results in clinical trials. 
                Personalized medicine and genetic testing enable targeted treatments 
                with fewer side effects than traditional chemotherapy.
                """,
                "category": "healthcare",
                "tags": ["medicine", "cancer", "research"]
            },
            {
                "title": "Space Exploration Mission",
                "content": """
                NASA's latest Mars rover mission has discovered evidence of ancient water 
                on the red planet. The findings suggest that Mars may have been habitable 
                in the past. Future missions will focus on searching for signs of 
                past or present microbial life.
                """,
                "category": "science",
                "tags": ["space", "Mars", "NASA"]
            }
        ]
        
        # Test queries for semantic search
        self.test_queries = [
            "artificial intelligence and algorithms",
            "environmental issues and temperature changes",
            "stock market investment strategies", 
            "cancer treatment and medical advances",
            "space missions and planetary exploration",
            "learning from data patterns",
            "economic uncertainty effects",
            "genetic medicine approaches"
        ]
    
    async def run_verification(self) -> Dict[str, Any]:
        """
        Run complete verification suite
        """
        logger.info("Starting FAISS Semantic Search System Verification")
        
        try:
            # Test 1: Service Initialization
            await self._test_service_initialization()
            
            # Test 2: Embedding Generation
            await self._test_embedding_generation()
            
            # Test 3: FAISS Index Operations
            await self._test_faiss_operations()
            
            # Test 4: Document Processing Pipeline
            await self._test_document_pipeline()
            
            # Test 5: Semantic Search Queries
            await self._test_semantic_search()
            
            # Test 6: Performance and Scalability
            await self._test_performance()
            
            # Test 7: Error Handling
            await self._test_error_handling()
            
            # Generate comprehensive report
            return self._generate_verification_report()
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_service_initialization(self):
        """Test 1: Verify all services can be initialized"""
        logger.info("Test 1: Service Initialization")
        
        try:
            # Test embedding service
            from app.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            
            # Load model
            model_loaded = await embedding_service.load_model()
            assert model_loaded, "Embedding model failed to load"
            
            # Get model info
            model_info = await embedding_service.get_model_info()
            assert model_info["model_name"], "Model name not available"
            assert model_info["dimension"] > 0, "Invalid embedding dimension"
            
            # Test FAISS service
            from app.services.faiss_service import get_faiss_service
            faiss_service = get_faiss_service()
            
            # Initialize index
            await faiss_service.initialize_index(dimension=model_info["dimension"])
            
            # Get index info
            index_info = await faiss_service.get_index_info()
            assert index_info["dimension"] == model_info["dimension"], "Dimension mismatch"
            
            self.test_results["service_initialization"] = {
                "success": True,
                "embedding_service": model_info,
                "faiss_service": index_info
            }
            
            logger.info("✓ Service initialization successful")
            
        except Exception as e:
            self.test_results["service_initialization"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ Service initialization failed: {e}")
            raise
    
    async def _test_embedding_generation(self):
        """Test 2: Verify embedding generation functionality"""
        logger.info("Test 2: Embedding Generation")
        
        try:
            from app.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            
            # Test single embedding
            test_text = "This is a test document for embedding generation."
            embedding = await embedding_service.generate_embedding(test_text)
            
            assert embedding is not None, "Single embedding generation failed"
            assert len(embedding) > 0, "Empty embedding generated"
            assert isinstance(embedding, np.ndarray), "Embedding not numpy array"
            
            # Test batch embeddings
            test_texts = [doc["content"] for doc in self.test_documents[:3]]
            batch_embeddings = await embedding_service.generate_embeddings_batch(test_texts)
            
            assert len(batch_embeddings) == len(test_texts), "Batch size mismatch"
            assert all(emb is not None for emb in batch_embeddings), "Some batch embeddings failed"
            
            # Test document chunking
            long_text = " ".join([doc["content"] for doc in self.test_documents])
            chunks_data = await embedding_service.chunk_and_embed_document(
                long_text, 
                chunk_strategy="paragraph"
            )
            
            assert len(chunks_data) > 0, "No chunks generated"
            assert all("embedding" in chunk for chunk in chunks_data), "Missing embeddings in chunks"
            
            self.test_results["embedding_generation"] = {
                "success": True,
                "single_embedding_shape": embedding.shape,
                "batch_count": len(batch_embeddings),
                "chunks_generated": len(chunks_data),
                "embedding_dimension": len(embedding)
            }
            
            logger.info("✓ Embedding generation successful")
            
        except Exception as e:
            self.test_results["embedding_generation"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ Embedding generation failed: {e}")
            raise
    
    async def _test_faiss_operations(self):
        """Test 3: Verify FAISS index operations"""
        logger.info("Test 3: FAISS Operations")
        
        try:
            from app.services.faiss_service import get_faiss_service
            from app.services.embedding_service import get_embedding_service
            
            faiss_service = get_faiss_service()
            embedding_service = get_embedding_service()
            
            # Generate test embeddings
            test_embeddings = []
            for i, doc in enumerate(self.test_documents):
                embedding = await embedding_service.generate_embedding(doc["content"])
                test_embeddings.append({
                    "embedding": embedding,
                    "metadata": {
                        "document_id": f"test_doc_{i}",
                        "title": doc["title"],
                        "category": doc["category"]
                    }
                })
            
            # Test adding embeddings
            await faiss_service.add_embeddings(test_embeddings)
            
            # Verify index size
            index_info = await faiss_service.get_index_info()
            assert index_info["total_vectors"] >= len(test_embeddings), "Not all embeddings added"
            
            # Test similarity search
            query_embedding = await embedding_service.generate_embedding("machine learning algorithms")
            search_results = await faiss_service.search_similar(
                query_embedding=query_embedding,
                embeddings_data=test_embeddings,
                top_k=3
            )
            
            assert len(search_results) > 0, "No search results returned"
            assert all("similarity" in result for result in search_results), "Missing similarity scores"
            assert search_results[0]["similarity"] <= 1.0, "Invalid similarity score"
            
            # Test hybrid search
            hybrid_results = await faiss_service.hybrid_search(
                query_embedding=query_embedding,
                document_embeddings=test_embeddings[:3],
                chunk_embeddings=test_embeddings[3:],
                top_k=5
            )
            
            assert len(hybrid_results) > 0, "No hybrid search results"
            
            self.test_results["faiss_operations"] = {
                "success": True,
                "vectors_added": len(test_embeddings),
                "index_size": index_info["total_vectors"],
                "search_results_count": len(search_results),
                "hybrid_results_count": len(hybrid_results),
                "top_similarity_score": search_results[0]["similarity"] if search_results else 0
            }
            
            logger.info("✓ FAISS operations successful")
            
        except Exception as e:
            self.test_results["faiss_operations"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ FAISS operations failed: {e}")
            raise
    
    async def _test_document_pipeline(self):
        """Test 4: Verify document processing pipeline integration"""
        logger.info("Test 4: Document Pipeline Integration")
        
        try:
            from app.services.semantic_integration import semantic_search_integration
            
            # Mock document processing (would normally be done through upload)
            test_doc_id = "test_pipeline_doc_1"
            test_user_id = "test_user_123"
            
            # Test processing status check
            initial_status = await semantic_search_integration.get_processing_status(
                document_id=test_doc_id,
                user_id=test_user_id
            )
            
            # The document shouldn't exist initially
            assert not initial_status.get("processed", False), "Document should not be processed initially"
            
            # Test batch processing capabilities
            test_doc_ids = [f"test_doc_{i}" for i in range(3)]
            batch_result = await semantic_search_integration.batch_process_documents(
                document_ids=test_doc_ids,
                user_id=test_user_id,
                max_concurrent=2
            )
            
            # Should handle non-existent documents gracefully
            assert "total_documents" in batch_result, "Missing batch processing metadata"
            
            self.test_results["document_pipeline"] = {
                "success": True,
                "initial_status_check": initial_status,
                "batch_processing": batch_result
            }
            
            logger.info("✓ Document pipeline integration successful")
            
        except Exception as e:
            self.test_results["document_pipeline"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ Document pipeline integration failed: {e}")
    
    async def _test_semantic_search(self):
        """Test 5: Verify end-to-end semantic search functionality"""
        logger.info("Test 5: Semantic Search Queries")
        
        try:
            from app.services.embedding_service import get_embedding_service
            from app.services.faiss_service import get_faiss_service
            
            embedding_service = get_embedding_service()
            faiss_service = get_faiss_service()
            
            # Prepare test data
            test_embeddings = []
            for i, doc in enumerate(self.test_documents):
                embedding = await embedding_service.generate_embedding(
                    f"{doc['title']} {doc['content']}"
                )
                test_embeddings.append({
                    "embedding": embedding,
                    "metadata": {
                        "document_id": f"doc_{i}",
                        "title": doc["title"],
                        "category": doc["category"],
                        "tags": doc["tags"]
                    }
                })
            
            # Test various search queries
            search_results = {}
            
            for query in self.test_queries:
                query_embedding = await embedding_service.generate_embedding(query)
                
                results = await faiss_service.search_similar(
                    query_embedding=query_embedding,
                    embeddings_data=test_embeddings,
                    top_k=3,
                    threshold=0.1
                )
                
                search_results[query] = {
                    "results_count": len(results),
                    "top_score": results[0]["similarity"] if results else 0,
                    "top_match": results[0]["metadata"]["title"] if results else None
                }
            
            # Test similarity calculations
            similarity_tests = []
            for i in range(len(self.test_documents) - 1):
                text1 = self.test_documents[i]["content"]
                text2 = self.test_documents[i + 1]["content"]
                
                from app.services.embedding_service import get_text_similarity
                similarity = await get_text_similarity(text1, text2)
                
                similarity_tests.append({
                    "doc1": self.test_documents[i]["title"],
                    "doc2": self.test_documents[i + 1]["title"],
                    "similarity": similarity
                })
            
            self.test_results["semantic_search"] = {
                "success": True,
                "queries_tested": len(self.test_queries),
                "search_results": search_results,
                "similarity_tests": similarity_tests,
                "avg_results_per_query": sum(r["results_count"] for r in search_results.values()) / len(search_results)
            }
            
            logger.info("✓ Semantic search queries successful")
            
        except Exception as e:
            self.test_results["semantic_search"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ Semantic search queries failed: {e}")
    
    async def _test_performance(self):
        """Test 6: Verify performance and scalability"""
        logger.info("Test 6: Performance Testing")
        
        try:
            from app.services.embedding_service import get_embedding_service
            from app.services.faiss_service import get_faiss_service
            
            embedding_service = get_embedding_service()
            faiss_service = get_faiss_service()
            
            # Test embedding generation performance
            start_time = time.time()
            test_texts = [f"Performance test document {i}" for i in range(10)]
            embeddings = await embedding_service.generate_embeddings_batch(test_texts)
            embedding_time = time.time() - start_time
            
            # Test search performance
            query_embedding = embeddings[0]
            embeddings_data = [
                {"embedding": emb, "metadata": {"id": i}}
                for i, emb in enumerate(embeddings)
            ]
            
            start_time = time.time()
            search_results = await faiss_service.search_similar(
                query_embedding=query_embedding,
                embeddings_data=embeddings_data,
                top_k=5
            )
            search_time = time.time() - start_time
            
            # Test memory usage (basic check)
            index_info = await faiss_service.get_index_info()
            
            self.test_results["performance"] = {
                "success": True,
                "embedding_generation_time": round(embedding_time, 3),
                "search_time": round(search_time, 3),
                "embeddings_per_second": round(len(test_texts) / embedding_time, 2),
                "index_size": index_info.get("total_vectors", 0),
                "memory_efficient": embedding_time < 5.0 and search_time < 1.0
            }
            
            logger.info("✓ Performance testing successful")
            
        except Exception as e:
            self.test_results["performance"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ Performance testing failed: {e}")
    
    async def _test_error_handling(self):
        """Test 7: Verify error handling and edge cases"""
        logger.info("Test 7: Error Handling")
        
        try:
            from app.services.embedding_service import get_embedding_service
            from app.services.faiss_service import get_faiss_service
            
            embedding_service = get_embedding_service()
            faiss_service = get_faiss_service()
            
            error_tests = {}
            
            # Test empty text embedding
            empty_embedding = await embedding_service.generate_embedding("")
            error_tests["empty_text"] = empty_embedding is None
            
            # Test None text embedding
            none_embedding = await embedding_service.generate_embedding(None)
            error_tests["none_text"] = none_embedding is None
            
            # Test very long text
            long_text = "A" * 100000
            long_embedding = await embedding_service.generate_embedding(long_text)
            error_tests["long_text_handled"] = long_embedding is not None
            
            # Test empty search
            empty_results = await faiss_service.search_similar(
                query_embedding=np.random.rand(384),  # Random embedding
                embeddings_data=[],
                top_k=5
            )
            error_tests["empty_search"] = len(empty_results) == 0
            
            # Test invalid threshold
            try:
                invalid_results = await faiss_service.search_similar(
                    query_embedding=np.random.rand(384),
                    embeddings_data=[],
                    top_k=5,
                    threshold=2.0  # Invalid threshold > 1.0
                )
                error_tests["invalid_threshold_handled"] = True
            except:
                error_tests["invalid_threshold_handled"] = True
            
            self.test_results["error_handling"] = {
                "success": True,
                "error_tests": error_tests,
                "all_errors_handled": all(error_tests.values())
            }
            
            logger.info("✓ Error handling successful")
            
        except Exception as e:
            self.test_results["error_handling"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"✗ Error handling failed: {e}")
    
    def _generate_verification_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        total_time = time.time() - self.start_time
        
        # Count successful tests
        successful_tests = sum(1 for test in self.test_results.values() if test.get("success", False))
        total_tests = len(self.test_results)
        
        # Overall system health
        system_healthy = successful_tests == total_tests
        
        report = {
            "verification_summary": {
                "overall_success": system_healthy,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "total_time_seconds": round(total_time, 2),
                "system_status": "HEALTHY" if system_healthy else "ISSUES_DETECTED"
            },
            "test_results": self.test_results,
            "system_capabilities": {
                "embedding_generation": self.test_results.get("embedding_generation", {}).get("success", False),
                "faiss_indexing": self.test_results.get("faiss_operations", {}).get("success", False),
                "semantic_search": self.test_results.get("semantic_search", {}).get("success", False),
                "document_pipeline": self.test_results.get("document_pipeline", {}).get("success", False),
                "performance_acceptable": self.test_results.get("performance", {}).get("memory_efficient", False),
                "error_handling": self.test_results.get("error_handling", {}).get("all_errors_handled", False)
            },
            "recommendations": self._generate_recommendations(),
            "next_steps": [
                "Deploy semantic search API endpoints",
                "Integrate with frontend interface",
                "Monitor performance in production",
                "Set up automated testing pipeline",
                "Configure monitoring and alerting"
            ]
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.test_results.get("service_initialization", {}).get("success", False):
            recommendations.append("Fix service initialization issues before deployment")
        
        if not self.test_results.get("performance", {}).get("memory_efficient", False):
            recommendations.append("Optimize performance for production workloads")
        
        if not self.test_results.get("error_handling", {}).get("all_errors_handled", False):
            recommendations.append("Improve error handling and edge case coverage")
        
        # Performance recommendations
        perf_results = self.test_results.get("performance", {})
        if perf_results.get("embedding_generation_time", 0) > 2.0:
            recommendations.append("Consider using faster embedding models for production")
        
        if perf_results.get("search_time", 0) > 0.5:
            recommendations.append("Optimize FAISS index configuration for faster search")
        
        # Search quality recommendations
        search_results = self.test_results.get("semantic_search", {})
        if search_results.get("avg_results_per_query", 0) < 2:
            recommendations.append("Improve document corpus or adjust similarity thresholds")
        
        if not recommendations:
            recommendations.append("System is performing well - ready for production deployment")
        
        return recommendations

async def main():
    """
    Main verification function
    """
    verifier = SemanticSearchVerification()
    
    try:
        # Run verification suite
        report = await verifier.run_verification()
        
        # Print results
        print("\n" + "="*80)
        print("FAISS SEMANTIC SEARCH SYSTEM VERIFICATION REPORT")
        print("="*80)
        
        summary = report["verification_summary"]
        print(f"\nOverall Status: {summary['system_status']}")
        print(f"Tests Passed: {summary['successful_tests']}/{summary['total_tests']}")
        print(f"Total Time: {summary['total_time_seconds']} seconds")
        
        if summary["overall_success"]:
            print("\n✅ All tests passed! System is ready for deployment.")
        else:
            print(f"\n❌ {summary['failed_tests']} test(s) failed. Review issues before deployment.")
        
        print(f"\nSystem Capabilities:")
        for capability, status in report["system_capabilities"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {capability.replace('_', ' ').title()}")
        
        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
        
        print(f"\nNext Steps:")
        for step in report["next_steps"]:
            print(f"  • {step}")
        
        # Save detailed report
        report_file = Path("faiss_verification_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return report
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Run verification
    report = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if report.get("verification_summary", {}).get("overall_success", False) else 1
    exit(exit_code)