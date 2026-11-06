#!/bin/sh
set -eu
/usr/sbin/nginx -t
/bin/systemctl reload nginx
if test -e /opt/xiaofeiyu/frp-uses-public-cert; then
    /bin/systemctl restart frps
fi
