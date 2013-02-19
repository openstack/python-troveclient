# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import re
import setuptools
import sys


# Get requirements from the first file that exists
def get_reqs_from_files(requirements_files):
    for requirements_file in requirements_files:
        if os.path.exists(requirements_file):
            with open(requirements_file, 'r') as fil:
                return fil.read().split('\n')
    return []


def parse_requirements(requirements_files=['requirements.txt',
                                           'tools/pip-requires']):
    requirements = []
    for line in get_reqs_from_files(requirements_files):
        # For the requirements list, we need to inject only the portion
        # after egg= so that distutils knows the package it's looking for
        # such as:
        # -e git://github.com/openstack/nova/master#egg=nova
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1',
                                line))
        # such as:
        # http://github.com/openstack/nova/zipball/master#egg=nova
        elif re.match(r'\s*https?:', line):
            requirements.append(re.sub(r'\s*https?:.*#egg=(.*)$', r'\1',
                                line))
        # -f lines are for index locations, and don't get used here
        elif re.match(r'\s*-f\s+', line):
            pass
        # argparse is part of the standard library starting with 2.7
        # adding it to the requirements list screws distro installs
        elif line == 'argparse' and sys.version_info >= (2, 7):
            pass
        else:
            requirements.append(line)

    return requirements


def read_file(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setuptools.setup(
    name="python-reddwarfclient",
    version="0.1.2",
    author="OpenStack",
    description="Rich client bindings for Reddwarf REST API.",
    long_description="""Rich client bindings for Reddwarf REST API.""",
    license="Apache License, Version 2.0",
    url="https://github.com/stackforge/python-reddwarfclient",
    packages=["reddwarfclient"],
    install_requires=parse_requirements(),
    test_suite="nose.collector",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python"
    ],
    entry_points={
        "console_scripts": ["reddwarf-cli = reddwarfclient.cli:main",
                            "reddwarf-mgmt-cli = reddwarfclient.mcli:main",
                           ]
    }
)
