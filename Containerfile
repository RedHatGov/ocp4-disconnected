FROM registry.access.redhat.com/ubi8/python-311:latest

USER root

RUN yum install --disablerepo=* --enablerepo=ubi-8-appstream-rpms --enablerepo=ubi-8-baseos-rpms -y \
        yum-utils \
    && rm -rf /var/cache/yum

COPY --chown=1001:0 Pipfile Pipfile.lock /opt/app-root/src
RUN pip3 install pipenv \
    && pipenv install --system --deploy

USER 1001
COPY --chown=1001:0 . /opt/app-root/src

VOLUME /mnt/data

ENTRYPOINT ["/opt/app-root/src/app/bundle.py", "--output-dir", "/mnt/data"]
