FROM nginx:alpine

# copy your custom nginx config from repo’s frontend/nginx.conf
COPY frontend/nginx.conf   /etc/nginx/nginx.conf

# copy all static assets from repo’s frontend/src
COPY frontend/src/         /usr/share/nginx/html
