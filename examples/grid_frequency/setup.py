from setuptools import setup, find_packages

setup(
    name="ogrid",
    version="1.0.0",
    description="Ô Grid Frequency Diagnostic Toolkit — real-time power grid anomaly classification",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="DR (tygtDc)",
    url="https://github.com/MMDR10/O-Grid-Diagnostics",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=["numpy>=1.20"],
    entry_points={
        "console_scripts": [
            "ogrid=ogrid.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
    ],
)
