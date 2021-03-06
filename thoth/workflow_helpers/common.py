#!/usr/bin/env python3
# thoth-workflow-helpers
# Copyright(C) 2020 Francesco Murdaca
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Common methods for all workflow helpers."""

import logging
import json

from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
from thoth.storages import GraphDatabase
from thoth.workflow_helpers.configuration import Configuration

_LOGGER = logging.getLogger(__name__)

prometheus_registry = CollectorRegistry()

database_schema_revision_script = Gauge(
    "thoth_database_schema_revision_script",
    "Thoth database schema revision from script",
    ["component", "revision", "env"],
    registry=prometheus_registry,
)


def retrieve_solver_document(document_path: str):
    """Retrieve solver document."""
    _LOGGER.info("Loading document from a local file: %r", document_path)
    with open(document_path, "r") as document_file:
        solver_document = json.loads(document_file.read())

    return solver_document


def store_messages(output_messages: list):
    """Store messages."""
    # Store message to file that need to be sent.
    with open("/mnt/workdir/messages_to_be_sent.json", "w") as json_file:
        json.dump(output_messages, json_file)

    if output_messages:
        _LOGGER.info(f"Successfully stored file with messages to be sent!: {output_messages}")


def send_metrics():
    """Send metrics to pushgateway."""
    pushgateway_url = Configuration.THOTH_METRICS_PUSHGATEWAY_URL
    deployment_name = Configuration.THOTH_DEPLOYMENT_NAME

    component_name = "workflow-helpers"

    if deployment_name:
        database_schema_revision_script.labels(
            component_name, GraphDatabase().get_script_alembic_version_head(), deployment_name
        ).inc()
    else:
        _LOGGER.warning("THOTH_DEPLOYMENT_NAME env variable is not set.")

    if pushgateway_url and deployment_name:
        try:
            _LOGGER.debug(f"Submitting metrics to Prometheus pushgateway {pushgateway_url}")
            push_to_gateway(
                pushgateway_url,
                job=component_name,
                registry=prometheus_registry,
            )
        except Exception as e:
            _LOGGER.exception(f"An error occurred pushing the metrics: {str(e)}")

    else:
        _LOGGER.warning("PROMETHEUS_PUSHGATEWAY_URL env variable is not set.")
