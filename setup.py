import os
from setuptools import setup, find_packages


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


setup(
    name='django-popolo',
    version=__import__('popolo').__version__,
    author='Guglielmo Celata',
    author_email='guglielmo@openpolis.it',
    packages=find_packages(),
    include_package_data=True,
    url='http://github.com/openpolis/django-popolo',
    license='Affero',
    description=u' '.join(__import__('popolo').__doc__.splitlines()).strip(),
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
    ],
    long_description=read_file('README.rst'),
    test_suite="runtests.runtests",
    zip_safe=False,
    install_requires=[
        "django-autoslug==1.8.0",
        "django-model-utils",
    ],
)
