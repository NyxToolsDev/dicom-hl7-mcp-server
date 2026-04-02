"""Integration tests for DIMSE client against fake PACS SCP.

These tests start a real in-process PACS server and test actual
DICOM network operations over localhost.
"""

import pytest

from tests.mocks.fake_pacs import fake_pacs_server  # noqa: F401

from dicom_hl7_mcp.pacs.dimse_client import DIMSEClient
from dicom_hl7_mcp.pacs.models import QueryFilters


@pytest.mark.slow
class TestDIMSEClientIntegration:
    """Integration tests against the fake PACS SCP."""

    def test_echo_succeeds(self, fake_pacs_server):
        host, port, ae_title = fake_pacs_server
        client = DIMSEClient(
            pacs_ae_title=ae_title,
            pacs_host=host,
            pacs_port=port,
            local_ae_title="TEST_SCU",
        )
        result = client.echo()
        assert result.success is True
        assert result.response_time_ms > 0
        assert "successful" in result.message.lower()

    def test_echo_fails_wrong_port(self):
        client = DIMSEClient(
            pacs_ae_title="NONEXISTENT",
            pacs_host="127.0.0.1",
            pacs_port=1,  # Should fail
            local_ae_title="TEST_SCU",
        )
        result = client.echo()
        assert result.success is False

    def test_find_returns_studies(self, fake_pacs_server):
        host, port, ae_title = fake_pacs_server
        client = DIMSEClient(
            pacs_ae_title=ae_title,
            pacs_host=host,
            pacs_port=port,
        )
        filters = QueryFilters(query_level="STUDY", limit=10)
        results = client.find(filters)
        assert len(results) > 0
        assert results[0].patient_name != ""
        assert results[0].study_instance_uid != ""

    def test_find_with_patient_id_filter(self, fake_pacs_server):
        host, port, ae_title = fake_pacs_server
        client = DIMSEClient(
            pacs_ae_title=ae_title,
            pacs_host=host,
            pacs_port=port,
        )
        filters = QueryFilters(
            query_level="STUDY",
            patient_id="MRN001",
            limit=10,
        )
        results = client.find(filters)
        assert len(results) >= 1
        assert results[0].patient_id == "MRN001"

    def test_find_with_accession_filter(self, fake_pacs_server):
        host, port, ae_title = fake_pacs_server
        client = DIMSEClient(
            pacs_ae_title=ae_title,
            pacs_host=host,
            pacs_port=port,
        )
        filters = QueryFilters(
            query_level="STUDY",
            accession_number="ACC001",
            limit=10,
        )
        results = client.find(filters)
        assert len(results) >= 1
        assert results[0].accession_number == "ACC001"

    def test_find_series_level(self, fake_pacs_server):
        host, port, ae_title = fake_pacs_server
        client = DIMSEClient(
            pacs_ae_title=ae_title,
            pacs_host=host,
            pacs_port=port,
        )
        filters = QueryFilters(
            query_level="SERIES",
            study_instance_uid="1.2.840.113619.2.55.3.999.1",
            limit=10,
        )
        results = client.find(filters)
        assert len(results) > 0
        assert results[0].modality != ""

    def test_find_respects_limit(self, fake_pacs_server):
        host, port, ae_title = fake_pacs_server
        client = DIMSEClient(
            pacs_ae_title=ae_title,
            pacs_host=host,
            pacs_port=port,
        )
        filters = QueryFilters(query_level="STUDY", limit=1)
        results = client.find(filters)
        assert len(results) == 1
