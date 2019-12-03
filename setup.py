from setuptools import setup, find_packages

setup(
	name='codeclose',
	version='1.0',
	packages=find_packages(),
	install_requires=[
		'cryptography >= 1.4.0'
	],
	entry_points={
        'console_scripts': ['codeclose = codeclose.__main__:main']
    },
	include_package_data=True
)
