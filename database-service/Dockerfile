FROM mysql:8.0

ENV MYSQL_ROOT_PASSWORD=password
ENV MYSQL_ALLOW_EMPTY_PASSWORD=true

COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 3306