"""
Setup configuration for simple-sqlalchemy
"""

from setuptools import setup, find_packages

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A simplified, enhanced SQLAlchemy package with common patterns and utilities."

# Core dependencies
install_requires = [
    "sqlalchemy>=1.4.0,<3.0.0",
    "typing-extensions>=4.0.0",
]

# Optional dependencies
extras_require = {
    "postgres": [
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.1.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=22.0.0",
        "isort>=5.0.0",
        "mypy>=1.0.0",
        "pre-commit>=2.0.0",
    ],
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "myst-parser>=0.18.0",
    ],
}

# All optional dependencies
extras_require["all"] = [
    dep for deps in extras_require.values() for dep in deps
]

setup(
    name="simple-sqlalchemy",
    version="0.1.0",
    author="Simple SQLAlchemy Contributors",
    author_email="contributors@simple-sqlalchemy.dev",
    description="A simplified, enhanced SQLAlchemy package with common patterns and utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/simple-sqlalchemy/simple-sqlalchemy",
    project_urls={
        "Bug Tracker": "https://github.com/simple-sqlalchemy/simple-sqlalchemy/issues",
        "Documentation": "https://simple-sqlalchemy.readthedocs.io/",
        "Source Code": "https://github.com/simple-sqlalchemy/simple-sqlalchemy",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    keywords="sqlalchemy orm database crud pagination search",
    include_package_data=True,
    zip_safe=False,
)
