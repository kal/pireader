pireader
========

A stab at making a personal replacement for Google Reader that runs on a
RaspberryPi

Pre-requisites
--------------

Most of the required packages are specified in requirements.txt for use
with pip. However the opml package has a dependency on lxml, which in
turn requires some C libraries to be present.

On a Debian system such as Ubuntu you will need a command like

apt-get install python-dev libxml2 libxml2-dev libxslt-dev

to ensure that the required library files are available *before* running:

pip install -f requirements.txt

otherwise installation of the opml package will fail.
