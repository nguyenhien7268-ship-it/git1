# setup.py
# Minimal setup for pytest imports

from setuptools import setup, find_packages

setup(
    name="xoso-das",
    version="11.2.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.4.3",
        "pytest-cov>=4.1.0",
    ],
)
