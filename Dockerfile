FROM bscwdc/dislib-base:1.0.0
LABEL org.opencontainers.image.authors="COMPSs Support <support-compss@bsc.es>"

WORKDIR /
COPY . dislib/

ENV PYTHONPATH=$PYTHONPATH:/dislib
ENV LC_ALL=C.UTF-8
RUN python3 -m pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade -r /dislib/requirements.txt

ENV COMPSS_LOAD_SOURCE false

# Expose SSH port and run SSHD
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
