"""PACS Connection Manager.

Wraps both DIMSE and DICOMweb clients behind a unified interface.
Routes operations to the appropriate client based on configured protocol.
"""

from __future__ import annotations

import logging
from typing import Any

from dicom_hl7_mcp.config import (
    DICOMWEB_AUTH_TYPE,
    DICOMWEB_PASSWORD,
    DICOMWEB_TOKEN,
    DICOMWEB_URL,
    DICOMWEB_USERNAME,
    LOCAL_AE_TITLE,
    PACS_AE_TITLE,
    PACS_HOST,
    PACS_PORT,
    get_pacs_protocol,
)
from dicom_hl7_mcp.pacs import _HAS_HTTPX, _HAS_PYNETDICOM, require_pacs_deps
from dicom_hl7_mcp.pacs.models import EchoResult, QueryFilters, RetrieveResult, SeriesResult, StudyResult

logger = logging.getLogger(__name__)

# Lazy-initialized clients
_dimse_client = None
_dicomweb_client = None


def _get_dimse_client():
    """Get or create the DIMSE client."""
    global _dimse_client
    if _dimse_client is None and _HAS_PYNETDICOM:
        from dicom_hl7_mcp.pacs.dimse_client import DIMSEClient

        _dimse_client = DIMSEClient(
            pacs_ae_title=PACS_AE_TITLE,
            pacs_host=PACS_HOST,
            pacs_port=PACS_PORT,
            local_ae_title=LOCAL_AE_TITLE,
        )
    return _dimse_client


def _get_dicomweb_client():
    """Get or create the DICOMweb client."""
    global _dicomweb_client
    if _dicomweb_client is None and _HAS_HTTPX:
        from dicom_hl7_mcp.pacs.dicomweb_client import DICOMwebClient

        _dicomweb_client = DICOMwebClient(
            base_url=DICOMWEB_URL,
            auth_type=DICOMWEB_AUTH_TYPE,
            token=DICOMWEB_TOKEN,
            username=DICOMWEB_USERNAME,
            password=DICOMWEB_PASSWORD,
        )
    return _dicomweb_client


def pacs_echo() -> EchoResult:
    """Test PACS connectivity using the configured protocol.

    Returns:
        EchoResult with connection status.
    """
    protocol = get_pacs_protocol()

    dep_check = require_pacs_deps(protocol)
    if dep_check:
        return EchoResult(success=False, protocol=protocol, message=dep_check)

    if protocol == "dimse":
        client = _get_dimse_client()
        if not client:
            return EchoResult(
                success=False, protocol="dimse",
                message="DIMSE client not available. Check PACS configuration.",
            )
        return client.echo()

    elif protocol == "dicomweb":
        client = _get_dicomweb_client()
        if not client:
            return EchoResult(
                success=False, protocol="dicomweb",
                message="DICOMweb client not available. Check PACS configuration.",
            )
        return client.echo()

    return EchoResult(
        success=False, protocol="none",
        message="No PACS connection configured. Set DICOM_HL7_PACS_HOST/PORT or DICOM_HL7_DICOMWEB_URL.",
    )


def pacs_find(filters: QueryFilters) -> list[StudyResult] | list[SeriesResult]:
    """Query PACS for studies or series using the configured protocol.

    Args:
        filters: Query parameters.

    Returns:
        List of results.
    """
    protocol = get_pacs_protocol()

    if protocol == "dimse":
        client = _get_dimse_client()
        return client.find(filters) if client else []
    elif protocol == "dicomweb":
        client = _get_dicomweb_client()
        return client.find(filters) if client else []
    return []


def pacs_get_metadata(
    study_instance_uid: str,
    series_instance_uid: str = "",
) -> list[dict[str, Any]]:
    """Retrieve study/series metadata from PACS.

    For DIMSE: performs a detailed C-FIND at series level.
    For DICOMweb: uses WADO-RS metadata endpoint.

    Args:
        study_instance_uid: The study UID.
        series_instance_uid: Optional series UID.

    Returns:
        List of metadata objects (format depends on protocol).
    """
    protocol = get_pacs_protocol()

    if protocol == "dicomweb":
        client = _get_dicomweb_client()
        if client:
            return client.get_metadata(study_instance_uid, series_instance_uid)
        return []

    elif protocol == "dimse":
        # For DIMSE, do a series-level C-FIND to get detailed metadata
        client = _get_dimse_client()
        if client:
            filters = QueryFilters(
                query_level="SERIES",
                study_instance_uid=study_instance_uid,
            )
            if series_instance_uid:
                filters.series_instance_uid = series_instance_uid
            results = client.find(filters)
            # Convert SeriesResult models to dicts for consistent return type
            return [r.model_dump() for r in results]
        return []

    return []


def pacs_move(
    study_instance_uid: str,
    destination_ae: str,
    series_instance_uid: str = "",
) -> RetrieveResult:
    """Initiate C-MOVE to send images to a destination AE.

    Only available via DIMSE protocol.

    Args:
        study_instance_uid: The study to retrieve.
        destination_ae: Where to send the images.
        series_instance_uid: Optional series UID for series-level retrieve.

    Returns:
        RetrieveResult with completion status.
    """
    protocol = get_pacs_protocol()

    if protocol != "dimse":
        return RetrieveResult(
            success=False,
            message="C-MOVE is only available via DIMSE protocol. Configure DICOM_HL7_PACS_HOST/PORT.",
            study_instance_uid=study_instance_uid,
            destination_ae=destination_ae,
        )

    client = _get_dimse_client()
    if not client:
        return RetrieveResult(
            success=False,
            message="DIMSE client not available.",
            study_instance_uid=study_instance_uid,
            destination_ae=destination_ae,
        )

    return client.move(study_instance_uid, destination_ae, series_instance_uid)
