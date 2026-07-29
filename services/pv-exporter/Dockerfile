FROM python:3.12-slim

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && useradd --system --create-home --uid 904 exporter

COPY exporter.py /app/exporter.py

USER exporter
EXPOSE 9114

ENTRYPOINT ["python", "/app/exporter.py"]
CMD ["--config", "/config/pvs.yaml", "--port", "9114"]
