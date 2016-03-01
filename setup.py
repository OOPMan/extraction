from distutils.core import setup

from setuptools import find_packages

description = """
Jormungand is a plugin-based framework for creating applications that extract
data from varied sources, processing and validating the extracted data and then
storing it again in a common format.
""",

setup(
    name='jormungand',
    version='1.0.2',
    packages=find_packages('./src'),
    package_dir={
        '': 'src'
    },
    entry_points={
        'console_scripts': [
            'jormungand = jormungand.__main__:main'
        ]
    },
    url='https://github.com/oopman/jormungand/',
    license='MIT',
    author='Adam Jorgensen',
    author_email='adam.jorgensen.za@gmail.com',
    description=description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: General',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'yapsy==1.11.223', 'pyyaml==3.11'
    ],
    extras_requires={
        'SQLAlchemyFlatStorage': ['sqlalchemy>=0.9.3', 'simplejson'],
    }
)
