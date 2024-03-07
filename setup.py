from setuptools import setup, find_packages

setup(
    name='gamercon-async',
    version='1.0.6',
    packages=find_packages(),
    install_requires=[
        'asyncio',
    ],
    python_requires='>=3.8',
    description='An async rcon protocol for video games.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='dkoz',
    author_email='koz@beskor.net',
    url='https://github.com/dkoz/gamercon-async',
)
