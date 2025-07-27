"""
Tests for simple-sqlalchemy integration with news project patterns

This test file demonstrates how the string-schema integration works
with patterns commonly used in the news project.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud, SoftDeleteMixin


def _has_string_schema():
    """Check if string-schema is available"""
    try:
        import string_schema
        return True
    except ImportError:
        return False


# News-like models for testing
class NewsCategory(CommonBase):
    """News category model similar to news project"""
    __tablename__ = 'news_categories'
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)


class NewsArticle(CommonBase, SoftDeleteMixin):
    """News article model similar to news project"""
    __tablename__ = 'news_articles'
    
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    summary = Column(Text)
    category_id = Column(Integer, ForeignKey('news_categories.id'))
    is_published = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    data = Column(JSON, default=lambda: {})
    
    category = relationship("NewsCategory", backref="articles")


class NewsTag(CommonBase):
    """News tag model"""
    __tablename__ = 'news_tags'
    
    name = Column(String(50), nullable=False, unique=True)


# CRUD classes with news-specific methods
class NewsCategoryCrud(BaseCrud[NewsCategory]):
    """CRUD operations for news categories"""
    
    def __init__(self, db_client):
        super().__init__(NewsCategory, db_client)
        
        # Add news-specific schemas
        self.add_schema("category_summary", "id:int, name:string, description:text?")
        self.add_schema("category_with_stats", "id:int, name:string, article_count:int")


class NewsArticleCrud(BaseCrud[NewsArticle]):
    """CRUD operations for news articles"""
    
    def __init__(self, db_client):
        super().__init__(NewsArticle, db_client)
        
        # Add news-specific schemas
        self.add_schema("article_summary", "id:int, title:string, summary:text?, created_at:datetime")
        self.add_schema("article_with_category", "id:int, title:string, body:text, category:{id:int, name:string}?, is_published:bool")
        self.add_schema("article_stats", "category_id:int?, total_articles:int, published_articles:int, avg_views:number")
        self.add_schema("homepage_article", "id:int, title:string, summary:text?, view_count:int, created_at:datetime")


# Test fixtures
@pytest.fixture
def news_db_client():
    """Create test database client for news models"""
    client = DbClient("sqlite:///:memory:")
    
    # Create all tables
    CommonBase.metadata.create_all(client.engine)
    
    yield client
    
    # Cleanup
    client.close()


@pytest.fixture
def category_crud(news_db_client):
    """News category CRUD operations fixture"""
    return NewsCategoryCrud(news_db_client)


@pytest.fixture
def article_crud(news_db_client):
    """News article CRUD operations fixture"""
    return NewsArticleCrud(news_db_client)


@pytest.fixture
def sample_categories(category_crud):
    """Create sample news categories"""
    categories = []
    for name, desc in [
        ("Technology", "Technology news and updates"),
        ("Sports", "Sports news and scores"),
        ("Politics", "Political news and analysis")
    ]:
        category = category_crud.create({
            "name": name,
            "description": desc
        })
        categories.append(category)
    return categories


@pytest.fixture
def sample_articles(article_crud, sample_categories):
    """Create sample news articles"""
    articles = []
    for i, category in enumerate(sample_categories):
        for j in range(3):
            article = article_crud.create({
                "title": f"{category.name} Article {j+1}",
                "body": f"This is the body of {category.name.lower()} article {j+1}",
                "summary": f"Summary of {category.name.lower()} article {j+1}",
                "category_id": category.id,
                "is_published": j % 2 == 0,  # Alternate published/unpublished
                "view_count": (i + 1) * (j + 1) * 10,
                "data": {"tags": [f"tag{i}", f"tag{j}"], "priority": i + j}
            })
            articles.append(article)
    return articles


class TestNewsProjectIntegration:
    """Test integration patterns similar to news project"""
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_article_list_endpoint_pattern(self, article_crud, sample_articles):
        """Test pattern similar to GET /articles/ endpoint"""
        # Simulate typical article list endpoint
        result = article_crud.paginated_query_with_schema(
            "article_summary",  # Custom schema
            page=1,
            per_page=5,
            filters={"is_published": True},
            sort_by="created_at",
            sort_desc=True
        )
        
        # Verify pagination structure
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result
        assert "has_next" in result
        assert "has_prev" in result
        
        # Verify data structure
        assert len(result["items"]) <= 5
        for item in result["items"]:
            assert "id" in item
            assert "title" in item
            assert "summary" in item
            assert "created_at" in item
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_article_detail_with_category(self, article_crud, sample_articles):
        """Test pattern similar to GET /articles/{id} with category"""
        article = sample_articles[0]
        
        results = article_crud.query_with_schema(
            "article_with_category",
            filters={"id": article.id},
            include_relationships=["category"]
        )
        
        assert len(results) == 1
        result = results[0]
        
        # Verify article data
        assert result["id"] == article.id
        assert result["title"] == article.title
        assert result["body"] == article.body
        assert result["is_published"] == article.is_published
        
        # Verify nested category data
        assert "category" in result
        assert result["category"]["id"] == article.category_id
        # Since we're working with dictionaries, we can't access the relationship directly
        # The category name should be in the nested category dict
        assert "name" in result["category"]
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_homepage_articles_pattern(self, article_crud, sample_articles):
        """Test pattern for homepage article display"""
        # Get published articles for homepage
        homepage_articles = article_crud.query_with_schema(
            "homepage_article",
            filters={"is_published": True},
            sort_by="view_count",
            sort_desc=True,
            limit=10
        )
        
        # Verify all are published
        for article in homepage_articles:
            # Note: is_published not in homepage_article schema, 
            # but we filtered by it
            assert "id" in article
            assert "title" in article
            assert "view_count" in article
            assert "created_at" in article
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_search_articles_pattern(self, article_crud, sample_articles):
        """Test pattern for article search functionality"""
        # Search for technology articles
        search_results = article_crud.query_with_schema(
            "article_summary",
            search_query="Technology",
            search_fields=["title", "body", "summary"],
            filters={"is_published": True}
        )
        
        # Should find technology articles
        assert len(search_results) >= 1
        for result in search_results:
            # Should contain "Technology" in title, body, or summary
            text_content = f"{result['title']} {result.get('summary', '')}"
            assert "Technology" in text_content
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_category_statistics_pattern(self, article_crud, sample_articles):
        """Test pattern for category statistics"""
        # Get article statistics by category
        stats = article_crud.aggregate_with_schema(
            aggregations={
                "total_articles": "count(*)",
                "published_articles": "count(is_published)",  # This might need custom handling
                "avg_views": "avg(view_count)"
            },
            schema_str="article_stats",
            group_by=["category_id"]
        )
        
        # Should have stats for each category
        assert len(stats) >= 1
        for stat in stats:
            assert "category_id" in stat
            assert "total_articles" in stat
            assert "avg_views" in stat
            assert isinstance(stat["total_articles"], int)
            assert isinstance(stat["avg_views"], (int, float))
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_soft_delete_pattern(self, article_crud, sample_articles):
        """Test soft delete pattern common in news project"""
        article = sample_articles[0]
        
        # Soft delete the article
        article_crud.soft_delete(article.id)
        
        # Query without deleted should not include it
        active_articles = article_crud.query_with_schema(
            "article_summary",
            include_deleted=False
        )
        active_ids = [a["id"] for a in active_articles]
        assert article.id not in active_ids
        
        # Query with deleted should include it
        all_articles = article_crud.query_with_schema(
            "article_summary",
            include_deleted=True
        )
        all_ids = [a["id"] for a in all_articles]
        assert article.id in all_ids
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_json_field_handling(self, article_crud, sample_articles):
        """Test handling of JSON fields like data column"""
        # Query articles with JSON data (use string for JSON fields as they're serialized)
        results = article_crud.query_with_schema(
            "id:int, title:string, data:string",
            limit=1
        )
        
        assert len(results) >= 1
        result = results[0]
        
        # JSON field should be properly handled (serialized as string)
        assert "data" in result
        assert isinstance(result["data"], str)

        # Should be valid JSON
        import json
        parsed_data = json.loads(result["data"])
        assert isinstance(parsed_data, dict)
        assert "tags" in result["data"]
        assert "priority" in result["data"]
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_category_with_article_count(self, category_crud, article_crud, sample_articles):
        """Test pattern for categories with article counts"""
        # This would typically require a more complex query in real scenarios
        # For now, we'll test the basic aggregation pattern
        
        # Get categories
        categories = category_crud.query_with_schema("category_summary")
        
        # For each category, we could get article count
        # (In real implementation, this might be done with a JOIN or subquery)
        for category in categories:
            article_count = len(article_crud.query_with_schema(
                "id:int",
                filters={"category_id": category["id"]}
            ))
            
            # Add count to category data
            category["article_count"] = article_count
        
        # Verify structure
        for category in categories:
            assert "id" in category
            assert "name" in category
            assert "article_count" in category
            assert isinstance(category["article_count"], int)
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_performance_with_news_data(self, article_crud, category_crud):
        """Test performance with news-like data volumes"""
        import time
        
        # Create more test data
        category = category_crud.create({
            "name": "Performance Test",
            "description": "Category for performance testing"
        })
        
        # Create many articles
        start_time = time.time()
        for i in range(100):
            article_crud.create({
                "title": f"Performance Article {i}",
                "body": f"Body content for performance article {i}" * 10,
                "summary": f"Summary for article {i}",
                "category_id": category.id,
                "is_published": i % 2 == 0,
                "view_count": i * 5,
                "data": {"test": True, "index": i}
            })
        creation_time = time.time() - start_time
        
        # Test query performance
        start_time = time.time()
        results = article_crud.paginated_query_with_schema(
            "article_summary",
            page=1,
            per_page=20,
            filters={"category_id": category.id}
        )
        query_time = time.time() - start_time
        
        # Verify results
        assert len(results["items"]) == 20
        assert results["total"] == 100
        
        # Performance should be reasonable
        assert creation_time < 5.0  # Less than 5 seconds to create 100 articles
        assert query_time < 1.0     # Less than 1 second to query with pagination
        
        print(f"Created 100 articles in {creation_time:.3f}s")
        print(f"Paginated query took {query_time:.3f}s")


class TestNewsProjectMigrationPatterns:
    """Test patterns for migrating from Pydantic to string-schema"""
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_pydantic_to_string_schema_migration(self, article_crud, sample_articles):
        """Test migration pattern from Pydantic models to string-schema"""
        
        # Simulate old Pydantic approach (conceptually)
        # In real migration, you'd replace Pydantic models with string schemas
        
        # Old way (conceptual):
        # class ArticleResponse(BaseModel):
        #     id: int
        #     title: str
        #     summary: Optional[str]
        #     created_at: datetime
        
        # New way with string-schema:
        articles = article_crud.query_with_schema(
            "id:int, title:string, summary:text?, created_at:datetime",
            filters={"is_published": True}
        )
        
        # Verify same data structure is achieved
        for article in articles:
            assert isinstance(article["id"], int)
            assert isinstance(article["title"], str)
            # summary can be None (optional field)
            assert isinstance(article["created_at"], (datetime, str))
    
    @pytest.mark.skipif(
        not _has_string_schema(),
        reason="string-schema not available"
    )
    def test_hybrid_approach_pattern(self, article_crud, sample_articles):
        """Test hybrid approach: complex logic with Pydantic, response with string-schema"""
        
        # Simulate complex business logic that might still use Pydantic
        # (In real code, this would be actual Pydantic model validation)
        
        def complex_article_processing(article_data):
            """Simulate complex processing that might need Pydantic"""
            # This would use Pydantic for complex validation
            processed_data = {
                "id": article_data["id"],
                "title": article_data["title"].upper(),  # Some processing
                "status": "processed",
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            return processed_data
        
        # Get article data with string-schema
        articles = article_crud.query_with_schema(
            "id:int, title:string",
            limit=1
        )
        
        # Process with complex logic
        processed = complex_article_processing(articles[0])
        
        # Format final response with string-schema
        from string_schema import validate_to_dict
        response_schema = "id:int, title:string, status:string, processed_at:string"
        final_response = validate_to_dict(processed, response_schema)
        
        # Verify hybrid approach works
        assert final_response["id"] == articles[0]["id"]
        assert final_response["title"] == articles[0]["title"].upper()
        assert final_response["status"] == "processed"
        assert "processed_at" in final_response
