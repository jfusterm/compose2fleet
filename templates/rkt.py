
RKT_UNIT_TEMPLATE = '''\
[Unit]
Description={{ container_name }}
After=network-online.target {% if depends_on %}{% for dependency in depends_on %}{{ dependency }}.service {% endfor -%}{% endif -%}
{% if depends_on %}
Wants={% for dependency in depends_on %}{{ dependency }}.service {% endfor -%}
{% endif %}
Requires=network-online.target

[Service]
ExecStartPre=/usr/bin/rkt fetch --insecure-options=image docker://{{ image }}
ExecStart=/usr/bin/rkt run \\
    --hostname {{ container_name }} \\
    {%- if ports %}{% for port in ports %}
    --port {{ port }} \\
    {%- endfor -%}{% endif %}
    {%- if rkt_volumes %}{%- for rkt_volume in rkt_volumes %}
    {%- if rkt_volume['rkt_volume_type'] == "host" %}
    --volume {{ rkt_volume['rkt_volume_name'] }},kind=host,source={{ rkt_volume['rkt_host_volume'] }},readOnly={{ rkt_volume['read_only'] }} \\
    --mount volume={{ rkt_volume['rkt_volume_name'] }},target={{ rkt_volume['rkt_mount_point'] }} \\
    {%- else %}
    --volume {{ rkt_volume['rkt_host_volume'] }},kind=empty,readOnly={{ rkt_volume['read_only'] }}  \\
    --mount volume={{ rkt_volume['rkt_host_volume'] }},target={{ rkt_volume['rkt_mount_point'] }} \\
    {%- endif %}
    {%- endfor -%}{% endif %}
    {%- if environment %}{% for variable in environment %}
    --set-env {{ variable }} \\
    {%- endfor -%}{% endif %}
    {%- if networks %}{% for network in networks %}
    --net {{ network }} \\
    {%- endfor -%}{% endif %}
    docker://{{ image }}
    {%- if entrypoint %} \\
    --exec {{ entrypoint }} \\
    {%- if command %}
    -- {{ command }}
    {%- endif %}
    {%- endif %}
ExecStopPost=/usr/bin/rkt gc --grace-period=0
{%- if restart == "always" or restart == "no" or restart == "on-failure" %}
Restart={{ restart }}
{%- endif %}

[X-Fleet]
{%- if depends_on %}{%- for dependency in depends_on %}
MachineOf={{ dependency }}.service
{%- endfor -%}{% endif %}
'''

RKT_NET_TEMPLATE = '''\
{
    "name": "{{ rkt_network }}",
    "type": "bridge",
    "ipam": {
        "type": "host-local",
        "subnet": "{{ rkt_subnet }}"
    }
}
'''

def rkt_template():
    return RKT_UNIT_TEMPLATE

def rkt_net_template():
    return RKT_NET_TEMPLATE

