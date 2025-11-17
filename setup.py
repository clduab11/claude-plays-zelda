"""Setup configuration for claude-plays-zelda."""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="claude-plays-zelda",
    version="0.1.0",
    author="Claude AI Agent",
    description="An AI agent that autonomously plays Legend of Zelda using computer vision and Claude API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clduab11/claude-plays-zelda",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "anthropic>=0.39.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "opencv-python>=4.8.0",
        "pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "numpy>=1.24.0",
        "pyautogui>=0.9.54",
        "mss>=9.0.1",
        "Flask>=3.0.0",
        "Flask-SocketIO>=5.3.0",
        "twitchio>=2.9.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "loguru>=0.7.0",
        "tenacity>=8.2.0",
        "click>=8.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "ml": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "ultralytics>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "zelda-ai=claude_plays_zelda.cli:main",
        ],
    },
)
