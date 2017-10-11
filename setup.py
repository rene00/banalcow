from setuptools import setup

INSTALL_REQUIRES = list()
with open('requirements.txt') as requirements_file:
    for requirement in requirements_file:
        INSTALL_REQUIRES.append(requirement)
INSTALL_REQUIRES = list(set(INSTALL_REQUIRES))

setup(
    name='banalcow',
    packages=['banalcow'],
    version=0.1,
    install_requires=INSTALL_REQUIRES
)
