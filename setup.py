from setuptools import setup

install_requires = [
    "jsonref",
    "schema",
    "openpyxl>=2.6,!=3.0.2",
    "pytz",
    "xmltodict",
    "lxml",
    "odfpy",
]

setup(
    name="flattentool",
    version="0.12.0",
    author="Open Data Services",
    author_email="code@opendataservices.coop",
    packages=["flattentool"],
    scripts=["flatten-tool"],
    url="https://github.com/OpenDataServices/flatten-tool",
    license="MIT",
    description="Tools for generating CSV and other flat versions of the structured data",
    install_requires=install_requires,
    extras_require={"HTTP": ["requests"]},
)
