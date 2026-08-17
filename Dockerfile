FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY priser.js /usr/share/nginx/html/
COPY frontend/afgang-selfserve.html /usr/share/nginx/html/
EXPOSE 8080
RUN sed -i 's/listen\s*80;/listen 8080;/' /etc/nginx/conf.d/default.conf
