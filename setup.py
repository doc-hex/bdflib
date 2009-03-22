#!/usr/bin/python
from distutils.core import setup
from subprocess import Popen, PIPE
from os.path import dirname, join

def guess_version():
	git_repo = join(dirname(__file__), ".git")

	version_reader = Popen(
			[
				'git', '--git-dir', git_repo,
				'describe',
				# We only want to know about tags
				'--tags',
				# Tags that look like version numbers
				'--match', 'v*',
			],
			stdout=PIPE,
		)

	version_number = version_reader.communicate()[0]

	if version_reader.returncode == 0:
		# We found a version number.
		return version_number.strip()
	else:
		# Something went wrong, use a default value.
		return "0.0_unknown"


setup(
		name='bdflib',
		version=guess_version(),
		description="Library for working with BDF font files.",
		author="Timothy Allen",
		author_email="screwtape@froup.com",
		url='http://gitorious.org/projects/bdflib',
		packages=['bdflib', 'bdflib.test'],
		scripts=[
			'bin/bdflib-embolden',
			'bin/bdflib-fill',
			'bin/bdflib-merge',
			'bin/bdflib-passthrough',
		],
	)
