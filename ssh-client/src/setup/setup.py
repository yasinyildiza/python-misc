"""setup.py
IMPORTANT: pip installation is a prerequisite to run this setup script!

please make sure the followings are satisfied:
- you have installed pip (see get-pip.py)
- you have access to Internet
- you have access to python package repositories
- you have required privileges (i.e., administrator)

then, simply run the following command as a regular python script
for client:
  python setup.py client
for server:
  python setup.py server

you should see the SUCCESS message after completion of installation
if any error occurs, please note the package name(s),
and send an email to yasinyildiza@gmail.com
"""

from __future__ import print_function

import argparse
import os
import sys

try:
    import pip
except ImportError:
    sys.exit("""unable to import pip
        please run 'get-pip.py' first with required privileges
        then rerun this setup script""")

# pip install result
SUCCESS = 0

# check if OS is Windows
_IS_WINDOWS = os.name == 'nt'

def install(packages):
    """install the list of packages via pip
    """
    not_installed_packages = []
    for package in packages:
        result = pip.main(['install', package])
        if result != SUCCESS:
            print('unable to install {package}'.format(package=package))
            not_installed_packages.append(package)

    if not_installed_packages:
        print('ERROR: following packages could not be installed')
        for package in not_installed_packages:
            print('  {package}'.format(package=package))
    else:
        print('\n*********************************')
        print('*** SUCCESS: setup completed! ***')
        print('*********************************')

def main():
    """main function, entry point to execution
    """
    parser = argparse.ArgumentParser(description='statistics collector server')

    parser.add_argument('module', type=str, choices=['server', 'client'], help='module name')

    args = parser.parse_args()

    packages = []
    if args.module == 'server':
        packages.append('coverage') # code coverage by tests -- used only for unit tests
        packages.append('lxml') # xml parsing
        packages.append('pycrypto') # encryption
        packages.append('paramiko') # ssh and sftp connection
        packages.append('sqlalchemy') # database ORM
        packages.append('sqlalchemy_utils') # database utils
        packages.append('mysql-connector==2.1.4') # database connector

    elif args.module == 'client':
        packages.append('coverage') # code coverage by tests -- used only for unit tests
        packages.append('lxml') # xml parsing
        packages.append('pycrypto') # encryption
        packages.append('psutil') # platform independent system calls for statistics

        if _IS_WINDOWS:
            packages.append('pypiwin32') # Windows API for event logs

    install(packages)

if __name__ == '__main__':
    main()
