from setuptools import setup, find_packages
from os.path import basename, splitext
from glob import glob

setup(
    install_requires=[
        "certifi==2021.10.8",
        "charset-normalizer==2.0.10; python_version >= '3'",
        "idna==3.3; python_version >= '3'",
        "pyside2==5.15.2",
        "pysocks==1.7.1",
        "python-dateutil==2.8.2",
        "requests[socks]==2.27.1",
        "semver==2.13.0",
        "shiboken2==5.15.2; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4' and python_version < '3.10'",
        "six==1.16.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "typing-extensions==4.0.1",
        "urllib3==1.26.8; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4' and python_version < '4'",
    ],
    name="shortcircuit",
    license="MIT",
    packages=find_packages("src"),
    package_dir={"": "src"},
    data_files=[
        (
            "Lib/resources/database",
            [
                "resources/database/statics.csv",
                "resources/database/system_description.csv",
                "resources/database/system_jumps.csv",
            ],
        )
    ],
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    python_requires="==3.8.*",
)
