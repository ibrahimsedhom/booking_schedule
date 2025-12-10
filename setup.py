from setuptools import setup, find_packages

# Hardcoded version and requirements to avoid encoding issues during install
version = '0.0.1'

setup(
	name="booking_schedule",
	version=version,
	description="Booking Schedule Management",
	author="Transcorp",
	author_email="admin@transcorp.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=["frappe"]
)
