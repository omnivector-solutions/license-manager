import setuptools


VERSION = "21.2.0.dev0"


setuptools.setup(
    name='license-manager',
    version=VERSION,
    packages=setuptools.find_packages(
        include=["*"]
    ),
    license='GPLv3',
    long_description=open('README.md').read(),
    install_requires=['pyyaml', 'systemd'],
    entry_points={
        'console_scripts': [
            'license-server=license_manager.server.main:main',
            'license-agent=license_manager.agent.main:main',
        ],
    },
    include_package_data=True,
    python_requires='>=3.6.8',
)
