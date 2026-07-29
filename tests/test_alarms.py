"""Alarm system round-trip.

Publishes an alarm configuration message for an existing PV to the Kafka
config topic and waits for the Phoebus alarm server to answer with a state
message for that PV — proving Kafka, the alarm server, and its CA connection
to the IOCs all work.
"""

import json
import time
import uuid

from confluent_kafka import Consumer, Producer

from conftest import ALARM_TOPIC, KAFKA_BOOTSTRAP

PV = "LAB:CRYO:TC1:TEMP"
CONFIG_KEY = f"config:/{ALARM_TOPIC}/Integration/{PV}"
STATE_KEY = f"state:/{ALARM_TOPIC}/Integration/{PV}"


def test_alarm_server_round_trip():
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})
    payload = {
        "user": "integration-tests",
        "host": "tests",
        "description": "integration test entry",
        "enabled": True,
        "latching": False,
        "annunciating": False,
    }
    producer.produce(ALARM_TOPIC, key=CONFIG_KEY, value=json.dumps(payload))
    producer.flush(10)

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": f"tests-{uuid.uuid4()}",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([ALARM_TOPIC])

    try:
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            message = consumer.poll(2.0)
            if message is None or message.error():
                continue
            key = message.key().decode() if message.key() else ""
            if key == STATE_KEY:
                state = json.loads(message.value().decode())
                assert "severity" in state
                return
        raise AssertionError(
            f"No state message for {STATE_KEY} within 120 s — "
            "is the alarm server connected to Kafka and the IOCs?"
        )
    finally:
        consumer.close()
