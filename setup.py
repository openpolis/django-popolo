import os
from setuptools import setup, find_packages


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ""


setup_requirements = []
install_requirements = ["django-autoslug==1.9.4", "django-model-utils"]
test_requirements = ["Django==1.11", "Faker==0.8.13", "factory_boy==2.10.0", "mock==2.0.0"]

setup(
    name="django-popolo",
    version=__import__("popolo").__version__,
    author="Guglielmo Celata",
    author_email="guglielmo@openpolis.it",
    packages=find_packages(),
    include_package_data=True,
    url="http://github.com/openpolis/django-popolo",
    license="Affero",
    description=u" ".join(__import__("popolo").__doc__.splitlines()).strip(),
    classifiers=[
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Django",
        "Framework :: Django :: 1.10",
        "Framework :: Django :: 1.11",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
    ],
    long_description=read_file("README.rst"),
    test_suite="runtests.runtests",
    zip_safe=False,
    tests_require=test_requirements,
    install_requires=install_requirements,
    setup_requires=setup_requirements,
)
