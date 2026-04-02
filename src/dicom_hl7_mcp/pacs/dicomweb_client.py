"""DICOMweb client for QIDO-RS and WADO-RS operations.

Wraps httpx for HTTP-based DICOM operations against DICOMweb-capable PACS.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from dicom_hl7_mcp.pacs import _HAS_HTTPX
from dicom_hl7_mcp.pacs.models import EchoResult, QueryFilters, SeriesResult, StudyResult
from dicom_hl7_mcp.pacs.phi_guard import sanitize_exception

logger = logging.getLogger(__name__)

if _HAS_HTTPX:
    import httpx

# DICOMweb DICOM JSON tag numbers (as strings with leading zeros)
_TAG_STUDY_INSTANCE_UID = "0020000D"
_TAG_STUDY_DATE = "00080020"
_TAG_STUDY_TIME = "00080030"
_TAG_STUDY_DESCRIPTION = "00081030"
_TAG_ACCESSION_NUMBER = "00080050"
_TAG_PATIENT_NAME = "00100010"
_TAG_PATIENT_ID = "00100020"
_TAG_PATIENT_BIRTH_DATE = "00100030"
_TAG_PATIENT_SEX = "00100040"
_TAG_MODALITIES_IN_STUDY = "00080061"
_TAG_NUM_SERIES = "00201206"
_TAG_NUM_INSTANCES = "00201208"
_TAG_REFERRING_PHYSICIAN = "00080090"
_TAG_INSTITUTION_NAME = "00080080"
_TAG_SERIES_INSTANCE_UID = "0020000E"
_TAG_SERIES_NUMBER = "00200011"
_TAG_SERIES_DESCRIPTION = "0008103E"
_TAG_MODALITY = "00080060"
_TAG_NUM_SERIES_INSTANCES = "00201209"
_TAG_BODY_PART = "00180015"
_TAG_PROTOCOL_NAME = "00181030"
_TAG_STATION_NAME = "00081010"
_TAG_MANUFACTURER = "00080070"
_TAG_MANUFACTURER_MODEL = "00081090"


def _extract_value(dicom_json: dict, tag: str) -> str:
    """Extract a value from a DICOMweb JSON response element.

    DICOMweb returns values in the format:
    {"00100010": {"vr": "PN", "Value": [{"Alphabetic": "DOE^JOHN"}]}}

    Args:
        dicom_json: A single DICOM JSON object.
        tag: The tag key (e.g., "00100010").

    Returns:
        The extracted string value, or empty string.
    """
    element = dicom_json.get(tag, {})
    values = element.get("Value", [])
    if not values:
        return ""

    val = values[0]

    # PersonName has nested structure
    if isinstance(val, dict):
        if "Alphabetic" in val:
            return str(val["Alphabetic"])
        # Fall back to first string value in the dict
        for v in val.values():
            if isinstance(v, str):
                return v
        return str(val)

    return str(val)


class DICOMwebClient:
    """Client for DICOMweb (QIDO-RS, WADO-RS) operations."""

    def __init__(
        self,
        base_url: str,
        auth_type: str = "none",
        token: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_type = auth_type
        self.token = token
        self.username = username
        self.password = password
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create the httpx client with appropriate auth."""
        if self._client is None:
            headers = {
                "Accept": "application/dicom+json",
            }
            auth = None

            if self.auth_type == "bearer" and self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            elif self.auth_type == "basic" and self.username:
                auth = httpx.BasicAuth(self.username, self.password)

            self._client = httpx.Client(
                headers=headers,
                auth=auth,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    def echo(self) -> EchoResult:
        """Test DICOMweb connectivity by requesting the WADO-RS base URL.

        Returns:
            EchoResult with success status and response time.
        """
        client = self._get_client()
        start = time.monotonic()

        try:
            # Try QIDO-RS studies endpoint with limit=1 as a connectivity test
            resp = client.get(
                f"{self.base_url}/studies",
                params={"limit": 1, "includefield": "00080020"},
            )
            elapsed = (time.monotonic() - start) * 1000

            if resp.status_code in (200, 204):
                return EchoResult(
                    success=True,
                    protocol="dicomweb",
                    message=f"DICOMweb connection successful to {self.base_url}",
                    response_time_ms=round(elapsed, 1),
                )
            else:
                return EchoResult(
                    success=False,
                    protocol="dicomweb",
                    message=f"DICOMweb returned HTTP {resp.status_code}: {resp.reason_phrase}",
                    response_time_ms=round(elapsed, 1),
                )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return EchoResult(
                success=False,
                protocol="dicomweb",
                message=f"DICOMweb connection failed: {sanitize_exception(exc)}",
                response_time_ms=round(elapsed, 1),
            )

    def find(self, filters: QueryFilters) -> list[StudyResult] | list[SeriesResult]:
        """Query PACS via QIDO-RS.

        Args:
            filters: Query parameters.

        Returns:
            List of StudyResult or SeriesResult.
        """
        client = self._get_client()
        params = self._build_qido_params(filters)

        try:
            if filters.query_level == "SERIES" and filters.study_instance_uid:
                url = f"{self.base_url}/studies/{filters.study_instance_uid}/series"
            else:
                url = f"{self.base_url}/studies"

            resp = client.get(url, params=params)

            if resp.status_code == 204:
                return []  # No results

            if resp.status_code != 200:
                logger.error("QIDO-RS returned HTTP %d", resp.status_code)
                return []

            data = resp.json()
            if not isinstance(data, list):
                return []

            if filters.query_level == "SERIES":
                return [self._json_to_series_result(item) for item in data[:filters.limit]]
            else:
                return [self._json_to_study_result(item) for item in data[:filters.limit]]

        except Exception as exc:
            logger.error("QIDO-RS failed: %s", sanitize_exception(exc))
            return []

    def get_metadata(
        self,
        study_instance_uid: str,
        series_instance_uid: str = "",
    ) -> list[dict[str, Any]]:
        """Retrieve study or series metadata via WADO-RS.

        Args:
            study_instance_uid: The study UID.
            series_instance_uid: Optional series UID for series-level metadata.

        Returns:
            List of DICOM JSON metadata objects.
        """
        client = self._get_client()

        try:
            if series_instance_uid:
                url = f"{self.base_url}/studies/{study_instance_uid}/series/{series_instance_uid}/metadata"
            else:
                url = f"{self.base_url}/studies/{study_instance_uid}/metadata"

            resp = client.get(url)

            if resp.status_code != 200:
                logger.error("WADO-RS metadata returned HTTP %d", resp.status_code)
                return []

            data = resp.json()
            return data if isinstance(data, list) else []

        except Exception as exc:
            logger.error("WADO-RS metadata failed: %s", sanitize_exception(exc))
            return []

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def _build_qido_params(self, filters: QueryFilters) -> dict[str, str]:
        """Build QIDO-RS query parameters from filters."""
        params: dict[str, str] = {
            "limit": str(filters.limit),
        }

        if filters.patient_id:
            params["PatientID"] = filters.patient_id
        if filters.patient_name:
            params["PatientName"] = filters.patient_name
        if filters.accession_number:
            params["AccessionNumber"] = filters.accession_number
        if filters.study_date:
            params["StudyDate"] = filters.study_date
        if filters.modality:
            if filters.query_level == "SERIES":
                params["Modality"] = filters.modality
            else:
                params["ModalitiesInStudy"] = filters.modality
        if filters.study_description:
            params["StudyDescription"] = f"*{filters.study_description}*"
        if filters.study_instance_uid and filters.query_level != "SERIES":
            params["StudyInstanceUID"] = filters.study_instance_uid

        return params

    @staticmethod
    def _json_to_study_result(item: dict) -> StudyResult:
        """Convert a DICOMweb JSON object to a StudyResult."""
        return StudyResult(
            study_instance_uid=_extract_value(item, _TAG_STUDY_INSTANCE_UID),
            study_date=_extract_value(item, _TAG_STUDY_DATE),
            study_time=_extract_value(item, _TAG_STUDY_TIME),
            study_description=_extract_value(item, _TAG_STUDY_DESCRIPTION),
            accession_number=_extract_value(item, _TAG_ACCESSION_NUMBER),
            patient_name=_extract_value(item, _TAG_PATIENT_NAME),
            patient_id=_extract_value(item, _TAG_PATIENT_ID),
            patient_birth_date=_extract_value(item, _TAG_PATIENT_BIRTH_DATE),
            patient_sex=_extract_value(item, _TAG_PATIENT_SEX),
            modalities_in_study=_extract_value(item, _TAG_MODALITIES_IN_STUDY),
            number_of_series=_extract_value(item, _TAG_NUM_SERIES),
            number_of_instances=_extract_value(item, _TAG_NUM_INSTANCES),
            referring_physician_name=_extract_value(item, _TAG_REFERRING_PHYSICIAN),
            institution_name=_extract_value(item, _TAG_INSTITUTION_NAME),
        )

    @staticmethod
    def _json_to_series_result(item: dict) -> SeriesResult:
        """Convert a DICOMweb JSON object to a SeriesResult."""
        return SeriesResult(
            series_instance_uid=_extract_value(item, _TAG_SERIES_INSTANCE_UID),
            series_number=_extract_value(item, _TAG_SERIES_NUMBER),
            series_description=_extract_value(item, _TAG_SERIES_DESCRIPTION),
            modality=_extract_value(item, _TAG_MODALITY),
            number_of_instances=_extract_value(item, _TAG_NUM_SERIES_INSTANCES),
            body_part_examined=_extract_value(item, _TAG_BODY_PART),
            protocol_name=_extract_value(item, _TAG_PROTOCOL_NAME),
            station_name=_extract_value(item, _TAG_STATION_NAME),
            manufacturer=_extract_value(item, _TAG_MANUFACTURER),
            manufacturer_model_name=_extract_value(item, _TAG_MANUFACTURER_MODEL),
        )
