from setuptools import setup, find_packages

setup(
    name='MicrodropExtLibs',
    version='0.4',
    packages=find_packages(where='ext_libs'),  # Look for packages in ext_libs directory
    package_dir={'': 'ext_libs'},  # Treat ext_libs as the directory where packages are found
    description='External libraries for running Microdrop and Dropbot plugin',
    author='Vigneshwar Rajesh, Miguel Weerasinghe, Chrisitan Fobel',
    author_email='vignesh.rajesh@mail.utoronto.ca'
)

