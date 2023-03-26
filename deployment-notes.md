# Gamechanger Deployment Notes

Last updated 2023-03-16.

## Most Common Configuration files

- /etc/uwsgi/vassals/uwsgi.ini (which is a soft link to /home/deploy/gamechanger/gamechanger/uwsgi.ini)
- /etc/systemd/system/uwsgi.service (edit with: sudo systemctl edit uwsgi.service, follow on with   sudo systemctl daemon-reload )
- /etc/nginx/sites-available/gamechanger_nginx.conf
- /home/deploy/gamechanger/gamechanger/settings.py

## Most Common Log Files

- /var/log/nginx/access.log
- /var/log/nginx/error.log
- /var/log/uwsgi/gamechanger.log 
- /var/log/syslog
- /var/log/postgresql/postgresql-12-main.log 
- /var/log/gamechanger-spooler/last_import.log 

## Useful Systemctl Commands

- sudo systemctl restart uwsgi
- sudo systemctl status uwsgi
- sudo systemctl cat uwsgi
- sudo systemctl show uwsgi
- sudo systemctl edit uwsgi.service
- sudo systemctl daemon-reload

# Deployment Overview

Incoming HTTP requests on the www.gamechanger.eco host are served by a Nginx webserver. Nginx serves some (static) requests on its own, but most requests are passed down to uWSGI, an implementation of the WSGI API for webservers towards content processes. 

uWSGI is running in emperor mode, with a band of vassal workers (currently 10) to distribute work to. Each worker is running a Python/Django instance in a virtualenv. The uWSGI configuration controls which virtualenv is being entered, and which version of the Python VM that is launched. The Python env version in the virtualenv need to match for things to work, or you will get errors about missing modules. 

The uWSGI config file is potentially very large, and the exact parsing of this file depends on the uWSGI version, and errors are generally not reported. Instead unknown ini file directives are silently ignored. Difficult component to work with.

Nginx, uWSGI, PostgreSQL are automatically started at system start by systemd. The systemd configuration is key to make things work, and to control the running of the system. Systemd is also responsible for creating a number of /var/run directories that these services need.

## Component versions

- Ubuntu 20.04.6 LTS "focal"
- Python 3.8.10
- Django.VERSION (4, 1, 7, 'final', 0)
- PostgreSQL 12
- Uwsgi 2.0.21
- Nginx 1.18.0

These versions depend on each other in a complex web. A given version of Ubuntu supports certain versions of Python and Postgres. Certain versions of Python work with some versions of Django. Uwsgi is a chapter of its own.

## Useful reads

Here is a collection of articles I have found useful when working with the

- https://serverfault.com/questions/1039039/uwsgi-vassal-does-not-use-virtualenv
- https://stackoverflow.com/questions/12723016/uwsgi-specify-python-binary
- https://stackoverflow.com/questions/20176959/uwsgi-no-request-plugin-is-loaded-you-will-not-be-able-to-manage-requests/48299983#48299983
- https://serverfault.com/questions/1039039/uwsgi-vassal-does-not-use-virtualenv
- https://www.digitalocean.com/community/tutorials/how-to-set-up-uwsgi-and-nginx-to-serve-python-apps-on-centos-7
- https://uwsgi-docs.readthedocs.io/en/latest/Systemd.html
- https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files