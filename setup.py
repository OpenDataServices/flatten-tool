from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def run_compile_catalog(setuptools_command):
    from babel.messages.frontend import compile_catalog

    compiler = compile_catalog(setuptools_command.distribution)
    option_dict = setuptools_command.distribution.get_option_dict("compile_catalog")
    compiler.domain = [option_dict["domain"][1]]
    compiler.directory = option_dict["directory"][1]
    compiler.use_fuzzy = option_dict["use_fuzzy"][1]
    compiler.run()


# From https://stackoverflow.com/questions/40051076/compile-translation-files-when-calling-setup-py-install
class InstallWithCompile(install):
    def run(self):
        run_compile_catalog(self)
        super().run()


class DevelopWithCompile(develop):
    def run(self):
        run_compile_catalog(self)
        super().run()


install_requires = [
    "jsonref",
    "schema",
    "openpyxl>=2.6,!=3.0.2",
    "pytz",
    "xmltodict",
    "lxml",
    "odfpy",
    "backports-datetime-fromisoformat",
    "zodb",
    "zc.zlibstorage",
    "ijson",
]

setup(
    name="flattentool",
    version="0.20.1",
    author="Open Data Services",
    author_email="code@opendataservices.coop",
    packages=["flattentool"],
    scripts=["flatten-tool"],
    url="https://github.com/OpenDataServices/flatten-tool",
    license="MIT",
    description="Tools for generating CSV and other flat versions of the structured data",
    install_requires=install_requires,
    extras_require={"HTTP": ["requests"]},
    cmdclass={
        "install": InstallWithCompile,
        "develop": DevelopWithCompile,
    },
    package_data={"flattentool": ["locale/*/*/*.mo", "locale/*/*/*.po"]},
    setup_requires=["babel"],
)
