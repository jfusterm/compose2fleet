=============
compose2fleet
=============
compose2fleet is a simple script that transforms Docker Compose files into either Docker or Rkt Fleet unit files.

--------------------------------
Supported Docker Compose options
--------------------------------

Only the version 2 is supported.

* command
* container_name
* depends_on
* entrypoint
* environment
* networks
* ports
* restart
* volumes

----
Help
----
::

    $ compose2fleet -v
    usage: compose2fleet [-h] [-d | -r] [-o OUTPUT] [-v] file

    Convert Docker Compose files to CoreOS Fleet units

    positional arguments:
      file                  docker compose file

    optional arguments:
      -h, --help            show this help message and exit
      -d, --docker          select docker as the container runtime
      -r, --rkt             select rkt as the container runtime
      -o OUTPUT, --output OUTPUT
                            select the output directory
      -v                    show program's version number and exit

-----
Usage
-----

Given a `docker-compose.yml` file with either one or several services defined, `compose2fleet` will generate one `.service` unit file for each service. In case of using `rkt` as the container runtime, one `.conf` file will be generated for each user defined network.

::

    version: '2'
    services:
      grafana:
        image: jfusterm/grafana:latest
        container_name: grafana
        restart: on-failure
        ports:
        - "3000:3000"
        volumes:
        - /opt/grafana/data:/grafana/data
        - /opt/grafana/logs:/grafana/logs:ro
        depends_on:
        - influxdb
        - prometheus
      influxdb:
        image: jfusterm/influxdb:0.13.0
        container_name: influxdb
        restart: on-failure
        ports:
        - "2003:2003"
        - "8083:8083"
        - "8086:8086"
        volumes:
        - influxdb:/influxdb
      prometheus:
        image: jfusterm/prometheus:0.20.0
        container_name: prometheus
        restart: on-failure
        ports:
        - "9090:9090"
        volumes:
        - /prometheus
    volumes:
       influxdb:
    networks:
      gip_net:
        driver: bridge

^^^^^^
Docker
^^^^^^

Transforming the `docker-compose.yml` using Docker as the container runtime.

::

    $ compose2fleet -d docker-compose.yml
    Docker service created: grafana.service
    Docker service created: prometheus.service
    Docker service created: influxdb.service

* Grafana service

::

    [Unit]
    Description=grafana
    After=docker.service influxdb.service prometheus.service
    Wants=influxdb.service prometheus.service
    Requires=docker.service

    [Service]
    ExecStartPre=-/usr/bin/docker rm -f grafana
    ExecStartPre=/usr/bin/docker pull jfusterm/grafana:latest
    ExecStart=/usr/bin/docker run \
        --name grafana \
        -p 3000:3000 \
        --restart on-failure \
        -v /opt/grafana/data:/grafana/data \
        -v /opt/grafana/logs:/grafana/logs:ro \
        jfusterm/grafana:latest
    ExecStop=/usr/bin/docker stop grafana

    [X-Fleet]
    MachineOf=influxdb.service
    MachineOf=prometheus.service

* Prometheus service

::

    [Unit]
    Description=prometheus
    After=docker.service
    Requires=docker.service

    [Service]
    ExecStartPre=-/usr/bin/docker rm -f prometheus
    ExecStartPre=/usr/bin/docker pull jfusterm/prometheus:0.20.0
    ExecStart=/usr/bin/docker run \
        --name prometheus \
        -p 9090:9090 \
        --restart on-failure \
        -v /prometheus \
        jfusterm/prometheus:0.20.0
    ExecStop=/usr/bin/docker stop prometheus

[X-Fleet]

* InfluxDB service

::

    [Unit]
    Description=influxdb
    After=docker.service
    Requires=docker.service

    [Service]
    ExecStartPre=-/usr/bin/docker rm -f influxdb
    ExecStartPre=/usr/bin/docker pull jfusterm/influxdb:0.13.0
    ExecStart=/usr/bin/docker run \
        --name influxdb \
        -p 2003:2003 \
        -p 8083:8083 \
        -p 8086:8086 \
        --restart on-failure \
        -v influxdb:/influxdb \
        jfusterm/influxdb:0.13.0
    ExecStop=/usr/bin/docker stop influxdb

    [X-Fleet]


^^^
Rkt
^^^

Transforming the `docker-compose.yml` using rkt as the container runtime.

::

    $ compose2fleet -r gip.yaml
    Created rkt network: gip_net.conf
    Rkt service created: prometheus.service
    Rkt service created: grafana.service
    Rkt service created: influxdb.service

A `.conf` file will be generated for each user defined network in the `docker-compose.yml` file. The network files should be put under `etc/rkt/net.d/`

::

    {
        "name": "gip_net",
        "type": "bridge",
        "ipam": {
            "type": "host-local",
            "subnet": "10.42.0.0/16"
        }
    }

* Grafana service

::

    [Unit]
    Description=grafana
    After=network-online.target influxdb.service prometheus.service
    Wants=influxdb.service prometheus.service
    Requires=network-online.target

    [Service]
    ExecStartPre=/usr/bin/rkt fetch --insecure-options=image docker://jfusterm/grafana:latest
    ExecStart=/usr/bin/rkt run \
        --hostname grafana \
        --port 3000-tcp:3000 \
        --volume volume-opt-grafana-data,kind=host,source=/opt/grafana/data,readOnly=false \
        --mount volume=volume-opt-grafana-data,target=/grafana/data \
        --volume volume-opt-grafana-logs,kind=host,source=/opt/grafana/logs,readOnly=true \
        --mount volume=volume-opt-grafana-logs,target=/grafana/logs \
        docker://jfusterm/grafana:latest
    ExecStopPost=/usr/bin/rkt gc --grace-period=0
    Restart=on-failure

    [X-Fleet]
    MachineOf=influxdb.service
    MachineOf=prometheus.service

* Prometheus service

::

    [Unit]
    Description=prometheus
    After=network-online.target
    Requires=network-online.target

    [Service]
    ExecStartPre=/usr/bin/rkt fetch --insecure-options=image docker://jfusterm/prometheus:0.20.0
    ExecStart=/usr/bin/rkt run \
        --hostname prometheus \
        --port 9090-tcp:9090 \
        docker://jfusterm/prometheus:0.20.0
    ExecStopPost=/usr/bin/rkt gc --grace-period=0
    Restart=on-failure

    [X-Fleet]

* Influxdb service

::

    [Unit]
    Description=influxdb
    After=network-online.target
    Requires=network-online.target

    [Service]
    ExecStartPre=/usr/bin/rkt fetch --insecure-options=image docker://jfusterm/influxdb:0.13.0
    ExecStart=/usr/bin/rkt run \
        --hostname influxdb \
        --port 2003-tcp:2003 \
        --port 8083-tcp:8083 \
        --port 8086-tcp:8086 \
        --volume influxdb,kind=empty,readOnly=false  \
        --mount volume=influxdb,target=/influxdb \
        docker://jfusterm/influxdb:0.13.0
    ExecStopPost=/usr/bin/rkt gc --grace-period=0
    Restart=on-failure

    [X-Fleet]


----------------
Docker container
----------------

You can run compose2fleet in a Docker container

::

    $ docker pull jfusterm/compose2fleet
    $ docker run --rm -v $(pwd):/data/ jfusterm/compose2fleet docker-compose.yml

------------
Installation
------------

Download the latest release and execute

::

    $ python3 setup.py install
