import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="corvis",
    version="0.0.10",
    author="Tom Darby",
    author_email="tom@tmdarby.com",
    description="COVID-19 Rapid Visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ThomasDarby/COVIS/",
    packages=setuptools.find_packages(),
    classifiers=[
    	"Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    	"Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
    	'us',
    	'pandas',
    	'numpy',
    	'matplotlib',
    ],
)