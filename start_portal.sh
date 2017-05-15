#!/bin/bash

case $1 in
	start)
	source /home/.virtualenvs/portal/bin/activate
	cd ~/MSOPortal
	exec 2>&1 python manage.py runserver 0.0.0.0:80 &
	echo $! > /var/run/mso_portal.pid
	cd -
	;;
    stop)
	kill -9 `pidof python` ;;
    *)  
      echo "usage: MSO Portal {start|stop}" ;;
esac
exit 0
