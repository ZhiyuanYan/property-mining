import os
import subprocess

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop

BASEPATH = os.path.dirname(os.path.abspath(__file__))


class custom_develop(develop):
    def run(self):
        original_cwd = os.getcwd()

        # build trex lib and custom tf ops
        folders = [
            os.path.join(BASEPATH, 'property_mining/spec_encoder'),
        ]
        for folder in folders:
            os.chdir(folder)
            subprocess.check_call(['make'])

        os.chdir(original_cwd)

        develop.run(self)


class custom_install(install):
    def run(self):
        # install doesn't currently handle binary dependencies, so just use develop all the time
        assert False, 'please use develop instead of install'


setup(
    name='property_mining',
    packages=['metal'],
    install_requires=[
        'torch',
    ],
    cmdclass={
        'develop': custom_develop,
        'install': custom_install,
    }
)
