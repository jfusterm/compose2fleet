
DOCKER_UNIT_TEMPLATE = '''\
[Unit]
Description={{ container_name }}
After=docker.service {% if depends_on %}{% for dependency in depends_on %}{{ dependency }}.service {% endfor -%}{% endif -%}
{% if depends_on %}
Wants={% for dependency in depends_on %}{{ dependency }}.service {% endfor -%}
{% endif %}
Requires=docker.service

[Service]
ExecStartPre=-/usr/bin/docker rm -f {{ container_name }}
{%- if networks %}{%- for network in networks %}
ExecStartPre=-/usr/bin/docker network create {{ network }}
{%- endfor -%}{% endif %}
ExecStartPre=/usr/bin/docker pull {{ image }}
ExecStart=/usr/bin/docker run \\
    --name {{ container_name }} \\
    {%- if ports %}{% for port in ports %}
    -p {{ port }} \\
    {%- endfor -%}{% endif %}
    {%- if restart %}
    --restart {{ restart }} \\
    {%- endif -%}
    {%- if volumes %}{% for volume in volumes %}
    -v {{ volume }} \\
    {%- endfor -%}{% endif %}
    {%- if environment %}{% for variable in environment %}
    -e {{ variable }} \\
    {%- endfor -%}{% endif %}
    {%- if networks %}{% for network in networks %}
    --net {{ network }} \\
    {%- endfor -%}{% endif %}
    {%- if entrypoint %}
    --entrypoint {{ entrypoint }} \\
    {%- endif %}
    {{ image }} {%- if command %} \\
    {{ command }}
    {%- endif %}
ExecStop=/usr/bin/docker stop {{ container_name }}

[X-Fleet]
{%- if depends_on %}{%- for dependency in depends_on %}
MachineOf={{ dependency }}.service
{%- endfor -%}{% endif %}
'''

def docker_template():
    return DOCKER_UNIT_TEMPLATE

