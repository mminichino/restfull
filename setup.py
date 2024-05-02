from setuptools import setup, find_packages
import restfull
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='restfull',
    version=restfull.__version__,
    packages=find_packages(exclude=['tests']),
    url='https://github.com/mminichino/restfull',
    license='MIT License',
    author='Michael Minichino',
    python_requires='>=3.8',
    install_requires=[
        "attrs>=23.1.0",
        "requests>=2.31.0",
        "aiohttp>=3.9.3",
        "pytoolbase>=1.0.1",
        "python-certifi-win32>=1.6.1",
        "certifi>=2023.5.7"
    ],
    author_email='info@unix.us.com',
    description='Python REST API Frontend',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=["utilities", "rest", "api"],
    classifiers=[
          "Development Status :: 5 - Production/Stable",
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Topic :: Software Development :: Libraries",
          "Topic :: Software Development :: Libraries :: Python Modules"],
)
