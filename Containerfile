FROM registry.access.redhat.com/ubi8/python-311:latest

ENV PYTHONPATH=/opt/app-root/src:$PYTHONPATH

USER root

RUN yum install --disablerepo=* --enablerepo=ubi-8-appstream-rpms --enablerepo=ubi-8-baseos-rpms -y \
        yum-utils \
    && rm -rf /var/cache/yum

COPY Pipfile Pipfile.lock /opt/app-root/src
RUN pip3 install --upgrade pip \
    && pip3 install pipenv \
    && pipenv install --system --deploy

COPY . /opt/app-root/src

VOLUME /mnt/data

ENTRYPOINT ["python3", "-m", "ocp4_disconnected.bundle", "--output-dir", "/mnt/data"]
