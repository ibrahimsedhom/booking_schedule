from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

from booking_schedule import __version__ as version

setup(
	name="booking_schedule",
	version=version,
	description="Booking Schedule Management",
	author="Transcorp",
	author_email="admin@transcorp.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
