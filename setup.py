"""Setup script for Claude Plays Zelda."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="claude-plays-zelda",
    version="0.1.0",
    author="clduab11",
    description="AI system that autonomously plays The Legend of Zelda using Claude API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clduab11/claude-plays-zelda",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "claude-zelda=main:main",
        ],
    },
)
