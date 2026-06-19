from setuptools import setup, find_packages

setup(
    name="pox",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pox=main:main",
        ],
    },
    python_requires=">=3.10",
)
