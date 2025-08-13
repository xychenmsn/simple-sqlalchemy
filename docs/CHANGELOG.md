# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Automatic Timezone Handling**: All datetime fields in string-schema operations now automatically include UTC timezone information for consistent, timezone-aware API responses
- Initial release of simple-sqlalchemy
- Core database client with connection management
- Generic CRUD operations with BaseCrud
- CommonBase and SoftDeleteMixin for models
- Advanced search and pagination capabilities
- Bulk operations support
- Many-to-many relationship helpers
- PostgreSQL-specific features including vector support
- Comprehensive test suite with 109 tests using SQLite in-memory databases
- Multiple test runners (pytest, Makefile, custom script)
- 64% test coverage with detailed reporting
- Full type hint support
- Complete .gitignore for Python projects

### Changed

- N/A (initial release)

### Deprecated

- N/A (initial release)

### Removed

- N/A (initial release)

### Fixed

- N/A (initial release)

### Security

- N/A (initial release)

## [0.1.0] - 2024-12-XX

### Added

- Initial package structure
- Core functionality extracted from common_lib
- Database-agnostic CRUD operations
- PostgreSQL vector support with pgvector integration
- Session management utilities
- Pagination and search helpers
- Comprehensive documentation and examples
- MIT license
- Development tooling setup (black, mypy, pytest)

[Unreleased]: https://github.com/simple-sqlalchemy/simple-sqlalchemy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/simple-sqlalchemy/simple-sqlalchemy/releases/tag/v0.1.0
