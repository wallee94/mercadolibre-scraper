# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name         = 'project',
    version      = '1.0',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = mercadolibre_scraper.settings']},
    package_data = {
        'mercadolibre_scraper': ['resources/*.txt']
    },
    zip_safe=True,
)
