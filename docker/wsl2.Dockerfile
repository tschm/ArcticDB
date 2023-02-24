ARG IMGTAG
FROM ${IMGTAG}

ARG LOCAL_USER_ID
ENV LOCAL_USER_ID=${LOCAL_USER_ID}

COPY requirements.txt /opt/arcticc/
RUN ["/usr/local/bin/entrypoint.sh", "/bin/bash", "-c", "grep -v 'ipykernel install' /tmp/install_pycxx | bash"]

COPY wsl2_entry.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/wsl2_entry.sh"]
