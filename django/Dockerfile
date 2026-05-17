FROM python:3.14.5-trixie
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /code

RUN apt-get update && \
    apt-get install -y \
      binutils \
      libproj-dev \
      gdal-bin \
      libgdal-dev \
      libgeos-dev \
      libsqlite3-mod-spatialite \
    && \
    apt-get -y autoremove && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

COPY requirements.in .
RUN pip install -r requirements.in
COPY . .
EXPOSE 8000

ENTRYPOINT ["/code/docker-entrypoint.sh"]
