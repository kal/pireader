pireader
========

A stab at making a personal replacement for Google Reader that runs on a
RaspberryPi. Right now its kind of basic - it has support for importing
a list of subscriptions in OPML format (such as you get when you use 
Google Takeout to get your data from Reader) as well as adding new feeds
one at a time. The categorization from your OPML file should also get
preserved.

Feeds themselves are processed via a cron job. Content is stored on
the file system, not in a database as this is built to run on a
humble Pi.

Django provides the web framework. If you already have Django running
on your Pi, then you can probably just add the reader app in there.

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


Acknowledgements
----------------

Icons used come from the excellent Silk set at famfamfam: 
  http://www.famfamfam.com/lab/icons/silk/

Many awesome Python packages were used to cobble this together. A big shout 
out to all the package creators and maintainers of the packages listed in
requirements.txt
