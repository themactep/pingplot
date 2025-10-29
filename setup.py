#!/usr/bin/env python3
"""Setup configuration for PingPlot."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pingplot",
    version="1.0.0",
    author="Paul Philippov",
    author_email="themactep@gmail.com",
    description="Visualize ping latency as a graph with CLI output support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/themactep/pingplot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "pingplot=src.pingplot:main",
        ],
    },
    extras_require={
        "image": ["matplotlib"],
    },
)

