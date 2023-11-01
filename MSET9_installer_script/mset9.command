#!/bin/sh
if which python3 >/dev/null; then
	# use exec here to release shell and thus sd card, allow it to be umounted
	exec python3 "$(cd "$(dirname "$0")" && pwd)/mset9.py"
else
	echo "Python 3 is not installed."
	echo "Please install Python 3 and try again."
	echo "https://www.python.org/downloads/"
	echo "Press ENTER to exit ..."
	read DUMMY
fi
