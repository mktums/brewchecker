from setuptools import setup, find_packages

setup(
    name='brewchecker',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'Click',
        'pycurl',
        'pip>=6.1.1',
    ],
    include_package_data=True,
    url='https://github.com/mktums/brewchecker',
    license='MIT',
    author='Mike Tums',
    author_email='mktums@gmail.com',
    description="brewchecker is a tool for checking Homebrew packages'availability, written in Python.",
    entry_points={
        'console_scripts': [
            'brewchecker = brewchecker.main:main',
        ]
    },
    long_description=open('README.rst').read()
)
