"""Pydantic models for PACS query parameters and results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PACSConnectionInfo(BaseModel):
    """Connection details for a PACS server."""

    protocol: str = Field(description="Protocol in use: 'dimse' or 'dicomweb'")
    ae_title: str = Field(default="", description="Remote AE title (DIMSE)")
    host: str = Field(default="", description="Remote host (DIMSE)")
    port: int = Field(default=0, description="Remote port (DIMSE)")
    local_ae_title: str = Field(default="DICOM_HL7_MCP", description="Local AE title (DIMSE)")
    dicomweb_url: str = Field(default="", description="DICOMweb base URL")


class QueryFilters(BaseModel):
    """Filters for a PACS study/series/instance query."""

    query_level: str = Field(default="STUDY", description="STUDY, SERIES, or INSTANCE")
    patient_id: str = Field(default="", description="Patient ID filter")
    patient_name: str = Field(default="", description="Patient name filter (supports wildcards)")
    accession_number: str = Field(default="", description="Accession number filter")
    study_date: str = Field(default="", description="Study date or range (YYYYMMDD or YYYYMMDD-YYYYMMDD)")
    modality: str = Field(default="", description="Modality filter (CT, MR, US, etc.)")
    study_description: str = Field(default="", description="Study description filter")
    study_instance_uid: str = Field(default="", description="Study Instance UID")
    series_instance_uid: str = Field(default="", description="Series Instance UID")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")


class StudyResult(BaseModel):
    """A single study returned from a PACS query."""

    study_instance_uid: str = ""
    study_date: str = ""
    study_time: str = ""
    study_description: str = ""
    accession_number: str = ""
    patient_name: str = ""
    patient_id: str = ""
    patient_birth_date: str = ""
    patient_sex: str = ""
    modalities_in_study: str = ""
    number_of_series: str = ""
    number_of_instances: str = ""
    referring_physician_name: str = ""
    institution_name: str = ""


class SeriesResult(BaseModel):
    """A single series returned from a PACS query."""

    series_instance_uid: str = ""
    series_number: str = ""
    series_description: str = ""
    modality: str = ""
    number_of_instances: str = ""
    body_part_examined: str = ""
    protocol_name: str = ""
    station_name: str = ""
    manufacturer: str = ""
    manufacturer_model_name: str = ""


class EchoResult(BaseModel):
    """Result of a PACS echo (connectivity test)."""

    success: bool
    protocol: str
    message: str
    response_time_ms: float = 0.0
    remote_ae: str = ""
    local_ae: str = ""


class RetrieveResult(BaseModel):
    """Result of a PACS retrieve (C-MOVE) operation."""

    success: bool
    message: str
    study_instance_uid: str = ""
    destination_ae: str = ""
    num_completed: int = 0
    num_failed: int = 0
    num_warning: int = 0
