import os
from setuptools import setup

version = '0.1.0'


# taken from django-registration
# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('requests_monitor'):
    # Ignore dirnames that start with '.'
    dirnames = [dirname for dirname in dirnames if not dirname.startswith('.')]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[17:] # Strip "requests_monitor/" or "requests_monitor\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))


setup(
    name='django-requests-monitor',
    version=version,
    description='Shows debug information about requests',
    long_description=open('README.rst').read(),
    author='Kirill Fomichev',
    author_email='fanatid@ya.ru',
    url='https://github.com/fanatid/django-requests-monitor',
    license='BSD',
    package_dir={'requests_monitor': 'requests_monitor'},
    packages=packages,
    package_data={'requests_monitor': data_files},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django-debug-toolbar',
    ],
)
