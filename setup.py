from setuptools import setup, find_packages

setup(name='foldersync',
      description='Client and Server implementations for folder synchronisation',
      author='Nikolay Stanchev',
      author_email='nikist97.ns@gmail.com',
      packages=find_packages(),
      install_requires=[
        "twisted==18.9.0",
        "watchdog==0.9.0"
      ])
