#!/usr/bin/env python3
"""
Quick validation script for simple-sqlalchemy string-schema integration

This script performs a quick smoke test to ensure the integration works correctly.
"""

import sys
import traceback
from datetime import datetime


def test_basic_functionality():
    """Test basic simple-sqlalchemy functionality"""
    print("🔍 Testing basic simple-sqlalchemy functionality...")
    
    try:
        from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
        from sqlalchemy import Column, String, Integer, Boolean
        
        # Define test model
        class TestUser(CommonBase):
            __tablename__ = 'test_users'
            name = Column(String(100), nullable=False)
            email = Column(String(100), nullable=False)
            is_active = Column(Boolean, default=True)
        
        # Define CRUD
        class TestUserCrud(BaseCrud[TestUser]):
            def __init__(self, db_client):
                super().__init__(TestUser, db_client)
        
        # Test database operations
        db = DbClient("sqlite:///:memory:")
        CommonBase.metadata.create_all(db.engine)
        
        user_crud = TestUserCrud(db)
        
        # Create user
        user = user_crud.create({
            "name": "Test User",
            "email": "test@example.com",
            "is_active": True
        })
        
        # Read user
        retrieved_user = user_crud.get_by_id(user.id)
        assert retrieved_user.name == "Test User"
        
        # List users
        users = user_crud.get_multi()
        assert len(users) == 1
        
        db.close()
        print("✅ Basic functionality works")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        traceback.print_exc()
        return False


def test_string_schema_integration():
    """Test string-schema integration"""
    print("🔍 Testing string-schema integration...")
    
    try:
        import string_schema
        print("✅ string-schema package available")
    except ImportError:
        print("⚠️ string-schema not available, skipping integration tests")
        return True
    
    try:
        from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
        from sqlalchemy import Column, String, Integer, Boolean
        
        # Define test model
        class TestArticle(CommonBase):
            __tablename__ = 'test_articles'
            title = Column(String(200), nullable=False)
            content = Column(String(1000), nullable=False)
            is_published = Column(Boolean, default=False)
            view_count = Column(Integer, default=0)
        
        # Define CRUD with string-schema methods
        class TestArticleCrud(BaseCrud[TestArticle]):
            def __init__(self, db_client):
                super().__init__(TestArticle, db_client)
        
        # Test database operations
        db = DbClient("sqlite:///:memory:")
        CommonBase.metadata.create_all(db.engine)
        
        article_crud = TestArticleCrud(db)
        
        # Create test articles
        for i in range(5):
            article_crud.create({
                "title": f"Test Article {i}",
                "content": f"Content for article {i}",
                "is_published": i % 2 == 0,
                "view_count": i * 10
            })
        
        # Test query_with_schema
        articles = article_crud.query_with_schema(
            "id:int, title:string, is_published:bool",
            filters={"is_published": True}
        )
        
        assert len(articles) >= 1
        for article in articles:
            assert isinstance(article, dict)
            assert "id" in article
            assert "title" in article
            assert "is_published" in article
            assert article["is_published"] is True
        
        print("✅ query_with_schema works")
        
        # Test paginated_query_with_schema
        result = article_crud.paginated_query_with_schema(
            "id:int, title:string, view_count:int",
            page=1,
            per_page=3
        )
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert len(result["items"]) <= 3
        
        print("✅ paginated_query_with_schema works")
        
        # Test aggregate_with_schema
        stats = article_crud.aggregate_with_schema(
            aggregations={"total": "count(*)", "avg_views": "avg(view_count)"},
            schema_str="total:int, avg_views:number"
        )
        
        assert len(stats) == 1
        assert "total" in stats[0]
        assert "avg_views" in stats[0]
        
        print("✅ aggregate_with_schema works")
        
        # Test custom schemas
        article_crud.add_schema("summary", "id:int, title:string")
        summary_articles = article_crud.query_with_schema("summary", limit=2)
        
        assert len(summary_articles) == 2
        for article in summary_articles:
            assert "id" in article
            assert "title" in article
            assert "content" not in article  # Should not be in summary
        
        print("✅ Custom schemas work")
        
        db.close()
        print("✅ String-schema integration works")
        return True
        
    except Exception as e:
        print(f"❌ String-schema integration failed: {e}")
        traceback.print_exc()
        return False


def test_predefined_schemas():
    """Test predefined schema generation"""
    print("🔍 Testing predefined schema generation...")
    
    try:
        import string_schema
    except ImportError:
        print("⚠️ string-schema not available, skipping predefined schema tests")
        return True
    
    try:
        from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
        from simple_sqlalchemy.helpers.string_schema import StringSchemaHelper
        from sqlalchemy import Column, String, Integer, Boolean, DateTime
        
        # Define test model with various field types
        class TestModel(CommonBase):
            __tablename__ = 'test_models'
            name = Column(String(100), nullable=False)
            email = Column(String(100), nullable=False)
            age = Column(Integer, nullable=True)
            is_active = Column(Boolean, default=True)
        
        db = DbClient("sqlite:///:memory:")
        CommonBase.metadata.create_all(db.engine)
        
        # Test schema helper
        helper = StringSchemaHelper(db, TestModel)
        
        # Test basic schema generation
        basic_schema = helper._generate_basic_schema()
        assert "id:int" in basic_schema
        assert "name:string" in basic_schema
        print("✅ Basic schema generation works")
        
        # Test full schema generation
        full_schema = helper._generate_full_schema()
        assert "id:int" in full_schema
        assert "name:string" in full_schema
        assert "email:" in full_schema  # Should detect email
        assert "age:int?" in full_schema  # Should be optional
        assert "is_active:bool" in full_schema
        print("✅ Full schema generation works")
        
        db.close()
        print("✅ Predefined schemas work")
        return True
        
    except Exception as e:
        print(f"❌ Predefined schema test failed: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling"""
    print("🔍 Testing error handling...")
    
    try:
        from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
        from sqlalchemy import Column, String
        
        class TestModel(CommonBase):
            __tablename__ = 'test_error_model'
            name = Column(String(100), nullable=False)
        
        class TestCrud(BaseCrud[TestModel]):
            def __init__(self, db_client):
                super().__init__(TestModel, db_client)
        
        db = DbClient("sqlite:///:memory:")
        CommonBase.metadata.create_all(db.engine)
        crud = TestCrud(db)
        
        # Test string-schema not available error handling
        try:
            # This should work if string-schema is available
            crud.query_with_schema("id:int, name:string")
            print("✅ String-schema methods available")
        except ImportError as e:
            if "string-schema is required" in str(e):
                print("✅ Proper error handling when string-schema not available")
            else:
                raise
        
        db.close()
        print("✅ Error handling works")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main validation function"""
    print("🧪 Simple-SQLAlchemy String-Schema Integration Validation")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("String-Schema Integration", test_string_schema_integration),
        ("Predefined Schemas", test_predefined_schemas),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        print("\n✅ Simple-SQLAlchemy with string-schema integration is working correctly!")
        print("\n📋 What this means:")
        print("  • Core simple-sqlalchemy functionality works")
        print("  • String-schema integration is functional")
        print("  • Predefined schemas are generated correctly")
        print("  • Error handling is proper")
        print("  • Ready for use in your news project!")
        
        return 0
    else:
        print("❌ Some validation tests failed!")
        print("\n🔧 Troubleshooting:")
        print("  • Check that all dependencies are installed")
        print("  • Ensure string-schema is available if testing integration")
        print("  • Review error messages above")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
