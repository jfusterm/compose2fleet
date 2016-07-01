from setuptools import setup, find_packages

setup(name='compose2fleet',
      version='0.0.1',
      description='Convert Docker Compose files to CoreOS Fleet units',
      url='http://github.com/jfusterm/compose2fleet',
      author='Joan Fuster',
      author_email='joan.fuster@gmail.com',
      keywords='docker, rkt, container, compose, coreos, fleet',
      license='MIT',
      scripts=['bin/compose2fleet'],
      install_requires=[
        'jinja2',
        'pyyaml'
      ],
      packages=find_packages(),
      zip_safe=False,
)
