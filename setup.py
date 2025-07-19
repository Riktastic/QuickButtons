#!/usr/bin/env python3
"""Setup script for QuickButtons."""

from setuptools import setup, find_packages
import os

# Read the contents of the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'docs', 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="quickbuttons",
    version="1.0.0",
    author="Rik Heijmann",
    author_email="rik@rik.blue",
    description="A modern, floating, always-on-top button panel for running scripts, opening websites, and playing music.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rikheijmann/quickbuttons",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        'src': ['assets/*'],
    },
    entry_points={
        'console_scripts': [
            'quickbuttons=src.main:main',
        ],
        'gui_scripts': [
            'quickbuttons-gui=src.main:main',
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/rikheijmann/quickbuttons/issues",
        "Source": "https://github.com/rikheijmann/quickbuttons",
        "Documentation": "https://github.com/rikheijmann/quickbuttons/blob/main/docs/README.md",
    },
) 