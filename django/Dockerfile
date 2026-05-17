FROM python:3.14.5-trixie
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /code

RUN apt-get update && \
    apt-get install -y \
      libgdal-dev \
      libsqlite3-mod-spatialite \
    && \
    apt-get -y autoremove && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.in .
RUN pip install -r requirements.in
COPY . .
EXPOSE 8000

ENTRYPOINT ["/code/docker-entrypoint.sh"]
