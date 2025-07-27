#!/usr/bin/env python3
"""
Traditional SQLAlchemy Operations Example

This example demonstrates when and how to use traditional SQLAlchemy operations:
- Working with model instances and relationships
- Complex business logic in model methods
- Transaction management
- Change tracking and model state
- When you need the full power of SQLAlchemy ORM

Use this approach for the 10% of cases that need advanced ORM features!
"""

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta


# Setup
print("=== Traditional SQLAlchemy Operations Demo ===")
import os
import time
# Use a unique database name to avoid conflicts
db_name = f"traditional_demo_{int(time.time())}.db"
db = DbClient(f"sqlite:///{db_name}")
print(f"✅ Connected to database: {db_name}")


# Define Models with Relationships
class Author(CommonBase):
    __tablename__ = 'authors'
    
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    bio = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship
    books = relationship("Book", back_populates="author", lazy="dynamic")
    
    def __repr__(self):
        return f"<Author(name='{self.name}', email='{self.email}')>"
    
    # Business logic methods
    def get_published_books_count(self):
        """Get count of published books by this author"""
        return self.books.filter_by(published=True).count()
    
    def get_recent_books(self, days=30):
        """Get books published in the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return self.books.filter(Book.published_at >= cutoff_date).all()
    
    def calculate_total_pages(self):
        """Calculate total pages across all published books"""
        total = 0
        for book in self.books.filter_by(published=True):
            if book.pages:
                total += book.pages
        return total
    
    def send_welcome_email(self):
        """Simulate sending welcome email"""
        print(f"📧 Sending welcome email to {self.name} at {self.email}")
        return True
    
    def deactivate_with_reason(self, reason):
        """Deactivate author with business logic"""
        self.active = False
        self.bio = f"[DEACTIVATED: {reason}] {self.bio or ''}"
        print(f"⚠️ Author {self.name} deactivated: {reason}")


class Book(CommonBase):
    __tablename__ = 'books'
    
    title = Column(String(200), nullable=False)
    isbn = Column(String(20), unique=True)
    pages = Column(Integer)
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    
    # Relationship
    author = relationship("Author", back_populates="books")
    
    def __repr__(self):
        return f"<Book(title='{self.title}', isbn='{self.isbn}')>"
    
    # Business logic methods
    def publish(self):
        """Publish the book with business logic"""
        if self.published:
            print(f"📚 Book '{self.title}' is already published")
            return False
        
        self.published = True
        self.published_at = datetime.now()
        print(f"🎉 Published book '{self.title}' by {self.author.name}")
        return True
    
    def unpublish(self, reason=""):
        """Unpublish the book"""
        if not self.published:
            print(f"📚 Book '{self.title}' is not published")
            return False
        
        self.published = False
        self.published_at = None
        print(f"📚 Unpublished book '{self.title}'" + (f": {reason}" if reason else ""))
        return True
    
    def get_reading_time_minutes(self, words_per_page=250, words_per_minute=200):
        """Estimate reading time based on pages"""
        if not self.pages:
            return None
        
        total_words = self.pages * words_per_page
        return round(total_words / words_per_minute)

CommonBase.metadata.create_all(db.engine)

# Create CRUD instances
author_crud = BaseCrud(Author, db)
book_crud = BaseCrud(Book, db)


# 1. Creating Model Instances with Relationships
print("\n=== 1. Creating Model Instances ===")

# Create authors using traditional approach
author1 = Author(
    name="Jane Smith",
    email="jane@example.com",
    bio="Bestselling fiction author with 10+ years experience"
)

author2 = Author(
    name="John Doe", 
    email="john@example.com",
    bio="Technical writer and software architect"
)

# Save using CRUD (which handles sessions)
author1_id = author_crud.create({
    "name": author1.name,
    "email": author1.email,
    "bio": author1.bio
})

author2_id = author_crud.create({
    "name": author2.name,
    "email": author2.email,
    "bio": author2.bio
})

print(f"✅ Created authors: {author1_id}, {author2_id}")


# 2. Working with Model Instances and Relationships
print("\n=== 2. Model Instances and Relationships ===")

# Get model instances (not dicts)
author1_instance = author_crud.get_by_id(author1_id)
author2_instance = author_crud.get_by_id(author2_id)

print(f"Author 1: {author1_instance}")
print(f"Author 2: {author2_instance}")

# Create books with relationships
book1_id = book_crud.create({
    "title": "The Great Adventure",
    "isbn": "978-1234567890",
    "pages": 320,
    "author_id": author1_id
})

book2_id = book_crud.create({
    "title": "Python Mastery Guide",
    "isbn": "978-0987654321", 
    "pages": 450,
    "author_id": author2_id
})

book3_id = book_crud.create({
    "title": "Mystery Novel",
    "isbn": "978-1111111111",
    "pages": 280,
    "author_id": author1_id,
    "published": False  # Draft
})

print(f"✅ Created books: {book1_id}, {book2_id}, {book3_id}")


# 3. Using Model Methods and Business Logic
print("\n=== 3. Model Methods and Business Logic ===")

# Get fresh instances to work with
author1 = author_crud.get_by_id(author1_id)
book1 = book_crud.get_by_id(book1_id)
book2 = book_crud.get_by_id(book2_id)

# Use model methods
author1.send_welcome_email()

# Publish books using business logic
book1.publish()
book2.publish()

# Update the instances in database
book_crud.update(book1.id, {"published": book1.published, "published_at": book1.published_at})
book_crud.update(book2.id, {"published": book2.published, "published_at": book2.published_at})

# Use relationship-based methods
print(f"📊 {author1.name} has {author1.get_published_books_count()} published books")
print(f"📊 {author1.name}'s total pages: {author1.calculate_total_pages()}")

# Get reading time
reading_time = book1.get_reading_time_minutes()
if reading_time:
    print(f"📖 '{book1.title}' estimated reading time: {reading_time} minutes")


# 4. Working with Relationships
print("\n=== 4. Working with Relationships ===")

# Access relationships (lazy loading)
print(f"Books by {author1.name}:")
for book in author1.books:
    status = "Published" if book.published else "Draft"
    print(f"  - '{book.title}' ({status}) - {book.pages} pages")

print(f"\nAuthor of '{book1.title}': {book1.author.name}")


# 5. Complex Queries with Model Instances
print("\n=== 5. Complex Queries with Model Instances ===")

# Get multiple instances with enhanced filtering
published_books = book_crud.get_multi(
    filters={
        "published": True,
        "pages": {">=": 300},  # Enhanced filtering still works!
        "author_id": {"not": None}
    },
    sort_by="published_at",
    sort_desc=True
)

print("Published books (300+ pages):")
for book in published_books:
    print(f"  - '{book.title}' by {book.author.name} ({book.pages} pages)")


# 6. Search with Model Instances
print("\n=== 6. Search with Model Instances ===")

# Search across fields
search_results = book_crud.search(
    search_query="python",
    search_fields=["title", "isbn"],
    filters={"published": True}
)

print("Search results for 'python':")
for book in search_results:
    print(f"  - '{book.title}' (ISBN: {book.isbn}) by {book.author.name}")


# 7. Batch Operations with Model Logic
print("\n=== 7. Batch Operations with Model Logic ===")

# Get all authors and apply business logic
all_authors = author_crud.get_multi(filters={"active": True})

print("Processing all active authors:")
for author in all_authors:
    book_count = author.get_published_books_count()
    total_pages = author.calculate_total_pages()
    
    print(f"  - {author.name}: {book_count} books, {total_pages} total pages")
    
    # Apply business logic based on metrics
    if book_count == 0:
        print(f"    ⚠️ {author.name} has no published books")
    elif total_pages > 500:
        print(f"    🏆 {author.name} is a prolific writer!")


# 8. Transaction-like Operations
print("\n=== 8. Transaction-like Operations ===")

# Complex operation that might need rollback
try:
    # Get author instance
    author = author_crud.get_by_id(author2_id)
    
    # Apply business logic
    if author.get_published_books_count() < 2:
        author.deactivate_with_reason("Insufficient publications")
        
        # Update in database
        author_crud.update(author.id, {
            "active": author.active,
            "bio": author.bio
        })
        
        print(f"✅ Successfully processed author {author.name}")
    else:
        print(f"✅ Author {author.name} meets publication requirements")
        
except Exception as e:
    print(f"❌ Error processing author: {e}")


# 9. Hybrid Approach - Mix with Schema Operations
print("\n=== 9. Hybrid Approach ===")

# Get SQLAlchemy instance for complex operations
author = author_crud.get_by_id(author1_id)

# Use SQLAlchemy features
author.send_welcome_email()
book_count = author.get_published_books_count()

# Convert to validated dict for API response
api_response = author_crud.to_dict(
    author, 
    "id:int, name:string, email:email, active:bool, created_at:datetime"
)

print("Hybrid approach - SQLAlchemy instance to API dict:")
print(f"  - Processed {author.name} (has {book_count} published books)")
print(f"  - API response: {api_response}")


# 10. When to Use Traditional SQLAlchemy
print("\n=== 10. When to Use Traditional SQLAlchemy ===")

print("✅ Use Traditional SQLAlchemy when you need:")
print("  - Complex business logic in model methods")
print("  - Relationship manipulation (adding/removing related objects)")
print("  - Change tracking and model state management")
print("  - Custom SQLAlchemy features (events, hybrid properties)")
print("  - Complex transactions across multiple models")
print("  - ORM-level validations and constraints")

print("\n❌ Avoid Traditional SQLAlchemy for:")
print("  - Simple API endpoints that return JSON")
print("  - Basic CRUD operations")
print("  - Data validation and type safety")
print("  - High-performance read operations")

print("\n🎉 Traditional SQLAlchemy Operations Complete!")
print("\nKey takeaways:")
print("- Use for complex business logic and relationships")
print("- Model methods encapsulate domain logic")
print("- Relationships provide powerful data access")
print("- Mix with string-schema for best of both worlds")
print("- Perfect for complex domain models and business rules!")

# Cleanup
print(f"\n🧹 Cleaning up database file: {db_name}")
try:
    os.remove(db_name)
    print("✅ Database file removed")
except:
    print("⚠️ Could not remove database file")
