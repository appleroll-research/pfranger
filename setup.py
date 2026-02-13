from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pfranger",
    version="0.7.5",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "torch",
        "scikit-learn",
        "joblib",
        "PyYAML",
        "tqdm",
        "jinja2",
        "promptforest"
    ],
    entry_points={
        'console_scripts': [
            'pfranger=ranger.cli:main',
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    description="CLI tool for auditing prompts using PromptForest",
)
