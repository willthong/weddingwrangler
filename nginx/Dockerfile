FROM jwilder/nginx-proxy:0.9

RUN ls -l /etc/nginx/vhost.d
RUN ls -l /etc/nginx/conf.d

COPY vhost.d/default /etc/nginx/vhost.d/default

COPY custom.conf /etc/nginx/conf.d/custom.conf
