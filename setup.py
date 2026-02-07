from setuptools import setup, find_packages

setup(
    name="promptforest-ranger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "torch",
        "transformers",
        "sentence-transformers",
        "xgboost",
        "scikit-learn",
        "joblib",
        "PyYAML",
        "tqdm",
        "jinja2"
    ],
    entry_points={
        'console_scripts': [
            'ranger=ranger.cli:main',
        ],
    },
    author="PromptForest Team",
    description="CLI tool for auditing prompts using PromptForest",
)
