"""DIMSE (traditional DICOM networking) client.

Wraps pynetdicom for C-ECHO, C-FIND, and C-MOVE operations.
Each operation opens a fresh association and closes it when done.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from dicom_hl7_mcp.pacs import _HAS_PYNETDICOM
from dicom_hl7_mcp.pacs.models import EchoResult, QueryFilters, RetrieveResult, SeriesResult, StudyResult
from dicom_hl7_mcp.pacs.phi_guard import sanitize_exception

logger = logging.getLogger(__name__)

if _HAS_PYNETDICOM:
    from pydicom.dataset import Dataset
    from pynetdicom import AE, debug_logger
    from pynetdicom.sop_class import (
        PatientRootQueryRetrieveInformationModelFind,
        PatientRootQueryRetrieveInformationModelMove,
        StudyRootQueryRetrieveInformationModelFind,
        StudyRootQueryRetrieveInformationModelMove,
        Verification,
    )


# DICOM tag constants for building query datasets
_STUDY_LEVEL_TAGS = {
    "StudyInstanceUID": (0x0020, 0x000D),
    "StudyDate": (0x0008, 0x0020),
    "StudyTime": (0x0008, 0x0030),
    "StudyDescription": (0x0008, 0x1030),
    "AccessionNumber": (0x0008, 0x0050),
    "PatientName": (0x0010, 0x0010),
    "PatientID": (0x0010, 0x0020),
    "PatientBirthDate": (0x0010, 0x0030),
    "PatientSex": (0x0010, 0x0040),
    "ModalitiesInStudy": (0x0008, 0x0061),
    "NumberOfStudyRelatedSeries": (0x0020, 0x1206),
    "NumberOfStudyRelatedInstances": (0x0020, 0x1208),
    "ReferringPhysicianName": (0x0008, 0x0090),
    "InstitutionName": (0x0008, 0x0080),
}

_SERIES_LEVEL_TAGS = {
    "SeriesInstanceUID": (0x0020, 0x000E),
    "SeriesNumber": (0x0020, 0x0011),
    "SeriesDescription": (0x0008, 0x103E),
    "Modality": (0x0008, 0x0060),
    "NumberOfSeriesRelatedInstances": (0x0020, 0x1209),
    "BodyPartExamined": (0x0018, 0x0015),
    "ProtocolName": (0x0018, 0x1030),
    "StationName": (0x0008, 0x1010),
    "Manufacturer": (0x0008, 0x0070),
    "ManufacturerModelName": (0x0008, 0x1090),
}


class DIMSEClient:
    """Client for traditional DICOM networking operations."""

    def __init__(
        self,
        pacs_ae_title: str,
        pacs_host: str,
        pacs_port: int,
        local_ae_title: str = "DICOM_HL7_MCP",
    ) -> None:
        self.pacs_ae_title = pacs_ae_title
        self.pacs_host = pacs_host
        self.pacs_port = pacs_port
        self.local_ae_title = local_ae_title

    def echo(self) -> EchoResult:
        """Send C-ECHO to verify PACS connectivity.

        Returns:
            EchoResult with success status and response time.
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(Verification)

        start = time.monotonic()
        try:
            assoc = ae.associate(
                self.pacs_host,
                self.pacs_port,
                ae_title=self.pacs_ae_title,
            )

            if assoc.is_established:
                status = assoc.send_c_echo()
                elapsed = (time.monotonic() - start) * 1000
                assoc.release()

                if status and status.Status == 0x0000:
                    return EchoResult(
                        success=True,
                        protocol="dimse",
                        message=f"C-ECHO successful to {self.pacs_ae_title}@{self.pacs_host}:{self.pacs_port}",
                        response_time_ms=round(elapsed, 1),
                        remote_ae=self.pacs_ae_title,
                        local_ae=self.local_ae_title,
                    )
                else:
                    status_val = status.Status if status else "no response"
                    return EchoResult(
                        success=False,
                        protocol="dimse",
                        message=f"C-ECHO returned status: 0x{status_val:04X}" if isinstance(status_val, int) else f"C-ECHO returned: {status_val}",
                        response_time_ms=round(elapsed, 1),
                        remote_ae=self.pacs_ae_title,
                        local_ae=self.local_ae_title,
                    )
            else:
                elapsed = (time.monotonic() - start) * 1000
                return EchoResult(
                    success=False,
                    protocol="dimse",
                    message=f"Association rejected by {self.pacs_ae_title}@{self.pacs_host}:{self.pacs_port}",
                    response_time_ms=round(elapsed, 1),
                    remote_ae=self.pacs_ae_title,
                    local_ae=self.local_ae_title,
                )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return EchoResult(
                success=False,
                protocol="dimse",
                message=f"Connection failed: {sanitize_exception(exc)}",
                response_time_ms=round(elapsed, 1),
                remote_ae=self.pacs_ae_title,
                local_ae=self.local_ae_title,
            )

    def find(self, filters: QueryFilters) -> list[StudyResult] | list[SeriesResult]:
        """Send C-FIND to query PACS.

        Args:
            filters: Query parameters.

        Returns:
            List of StudyResult or SeriesResult depending on query level.
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

        ds = self._build_query_dataset(filters)

        try:
            assoc = ae.associate(
                self.pacs_host,
                self.pacs_port,
                ae_title=self.pacs_ae_title,
            )

            if not assoc.is_established:
                logger.error("Association rejected for C-FIND")
                return []

            results: list[Any] = []
            responses = assoc.send_c_find(
                ds,
                StudyRootQueryRetrieveInformationModelFind,
            )

            count = 0
            for status, identifier in responses:
                if status and status.Status in (0xFF00, 0xFF01) and identifier:
                    if filters.query_level == "SERIES":
                        results.append(self._dataset_to_series_result(identifier))
                    else:
                        results.append(self._dataset_to_study_result(identifier))
                    count += 1
                    if count >= filters.limit:
                        break

            assoc.release()
            return results

        except Exception as exc:
            logger.error("C-FIND failed: %s", sanitize_exception(exc))
            return []

    def move(
        self,
        study_instance_uid: str,
        destination_ae: str,
        series_instance_uid: str = "",
    ) -> RetrieveResult:
        """Send C-MOVE to retrieve studies/series to a destination AE.

        Args:
            study_instance_uid: The study to retrieve.
            destination_ae: The AE title to send images to.
            series_instance_uid: Optional series UID for series-level retrieve.

        Returns:
            RetrieveResult with completion status.
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)

        ds = Dataset()
        ds.QueryRetrieveLevel = "SERIES" if series_instance_uid else "STUDY"
        ds.StudyInstanceUID = study_instance_uid
        if series_instance_uid:
            ds.SeriesInstanceUID = series_instance_uid

        try:
            assoc = ae.associate(
                self.pacs_host,
                self.pacs_port,
                ae_title=self.pacs_ae_title,
            )

            if not assoc.is_established:
                return RetrieveResult(
                    success=False,
                    message=f"Association rejected by {self.pacs_ae_title}",
                    study_instance_uid=study_instance_uid,
                    destination_ae=destination_ae,
                )

            responses = assoc.send_c_move(
                ds,
                destination_ae,
                StudyRootQueryRetrieveInformationModelMove,
            )

            completed = 0
            failed = 0
            warning = 0

            for status, identifier in responses:
                if status:
                    s = status.Status
                    if s == 0x0000:
                        # Final success
                        completed = getattr(status, "NumberOfCompletedSuboperations", completed)
                        failed = getattr(status, "NumberOfFailedSuboperations", failed)
                        warning = getattr(status, "NumberOfWarningSuboperations", warning)
                    elif s == 0xFF00:
                        # Pending
                        completed = getattr(status, "NumberOfCompletedSuboperations", completed)

            assoc.release()

            success = failed == 0
            msg = f"C-MOVE {'completed' if success else 'completed with errors'}: {completed} sent"
            if failed:
                msg += f", {failed} failed"
            if warning:
                msg += f", {warning} warnings"

            return RetrieveResult(
                success=success,
                message=msg,
                study_instance_uid=study_instance_uid,
                destination_ae=destination_ae,
                num_completed=completed,
                num_failed=failed,
                num_warning=warning,
            )

        except Exception as exc:
            return RetrieveResult(
                success=False,
                message=f"C-MOVE failed: {sanitize_exception(exc)}",
                study_instance_uid=study_instance_uid,
                destination_ae=destination_ae,
            )

    def _build_query_dataset(self, filters: QueryFilters) -> Dataset:
        """Build a pydicom Dataset for a C-FIND query."""
        ds = Dataset()
        ds.QueryRetrieveLevel = filters.query_level

        if filters.query_level == "STUDY":
            # Request all study-level return keys
            for name, tag in _STUDY_LEVEL_TAGS.items():
                setattr(ds, name, "")

            # Apply filters
            if filters.patient_id:
                ds.PatientID = filters.patient_id
            if filters.patient_name:
                ds.PatientName = filters.patient_name
            if filters.accession_number:
                ds.AccessionNumber = filters.accession_number
            if filters.study_date:
                ds.StudyDate = filters.study_date
            if filters.modality:
                ds.ModalitiesInStudy = filters.modality
            if filters.study_description:
                ds.StudyDescription = f"*{filters.study_description}*"
            if filters.study_instance_uid:
                ds.StudyInstanceUID = filters.study_instance_uid

        elif filters.query_level == "SERIES":
            # Series-level requires StudyInstanceUID
            ds.StudyInstanceUID = filters.study_instance_uid
            for name, tag in _SERIES_LEVEL_TAGS.items():
                setattr(ds, name, "")
            if filters.modality:
                ds.Modality = filters.modality
            if filters.series_instance_uid:
                ds.SeriesInstanceUID = filters.series_instance_uid

        return ds

    @staticmethod
    def _dataset_to_study_result(ds: Dataset) -> StudyResult:
        """Convert a pydicom Dataset from C-FIND to a StudyResult."""
        return StudyResult(
            study_instance_uid=str(getattr(ds, "StudyInstanceUID", "")),
            study_date=str(getattr(ds, "StudyDate", "")),
            study_time=str(getattr(ds, "StudyTime", "")),
            study_description=str(getattr(ds, "StudyDescription", "")),
            accession_number=str(getattr(ds, "AccessionNumber", "")),
            patient_name=str(getattr(ds, "PatientName", "")),
            patient_id=str(getattr(ds, "PatientID", "")),
            patient_birth_date=str(getattr(ds, "PatientBirthDate", "")),
            patient_sex=str(getattr(ds, "PatientSex", "")),
            modalities_in_study=str(getattr(ds, "ModalitiesInStudy", "")),
            number_of_series=str(getattr(ds, "NumberOfStudyRelatedSeries", "")),
            number_of_instances=str(getattr(ds, "NumberOfStudyRelatedInstances", "")),
            referring_physician_name=str(getattr(ds, "ReferringPhysicianName", "")),
            institution_name=str(getattr(ds, "InstitutionName", "")),
        )

    @staticmethod
    def _dataset_to_series_result(ds: Dataset) -> SeriesResult:
        """Convert a pydicom Dataset from C-FIND to a SeriesResult."""
        return SeriesResult(
            series_instance_uid=str(getattr(ds, "SeriesInstanceUID", "")),
            series_number=str(getattr(ds, "SeriesNumber", "")),
            series_description=str(getattr(ds, "SeriesDescription", "")),
            modality=str(getattr(ds, "Modality", "")),
            number_of_instances=str(getattr(ds, "NumberOfSeriesRelatedInstances", "")),
            body_part_examined=str(getattr(ds, "BodyPartExamined", "")),
            protocol_name=str(getattr(ds, "ProtocolName", "")),
            station_name=str(getattr(ds, "StationName", "")),
            manufacturer=str(getattr(ds, "Manufacturer", "")),
            manufacturer_model_name=str(getattr(ds, "ManufacturerModelName", "")),
        )
