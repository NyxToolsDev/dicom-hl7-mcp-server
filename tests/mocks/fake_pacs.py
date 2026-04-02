"""Fake PACS SCP for integration testing.

Creates an in-process pynetdicom SCP that responds to C-ECHO and C-FIND
with canned test data. Runs on localhost with an ephemeral port.
"""

from __future__ import annotations

import threading
from typing import Generator

import pytest
from pydicom.dataset import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelFind,
    Verification,
)


# ---------------------------------------------------------------
# Sample datasets for C-FIND responses
# ---------------------------------------------------------------

def _make_study_dataset(
    patient_name: str = "DOE^JOHN",
    patient_id: str = "MRN001",
    accession: str = "ACC001",
    study_date: str = "20260401",
    modality: str = "CT",
    description: str = "CT CHEST W CONTRAST",
    study_uid: str = "1.2.840.113619.2.55.3.999.1",
) -> Dataset:
    """Create a sample study-level C-FIND response dataset."""
    ds = Dataset()
    ds.QueryRetrieveLevel = "STUDY"
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.PatientBirthDate = "19800115"
    ds.PatientSex = "M"
    ds.AccessionNumber = accession
    ds.StudyDate = study_date
    ds.StudyTime = "143025"
    ds.StudyDescription = description
    ds.StudyInstanceUID = study_uid
    ds.ModalitiesInStudy = modality
    ds.NumberOfStudyRelatedSeries = "3"
    ds.NumberOfStudyRelatedInstances = "245"
    ds.ReferringPhysicianName = "SMITH^JANE"
    ds.InstitutionName = "GENERAL HOSPITAL"
    return ds


def _make_series_dataset(
    series_uid: str = "1.2.840.113619.2.55.3.999.1.1",
    modality: str = "CT",
    description: str = "AXIAL 5mm",
    series_number: str = "2",
) -> Dataset:
    """Create a sample series-level C-FIND response dataset."""
    ds = Dataset()
    ds.QueryRetrieveLevel = "SERIES"
    ds.SeriesInstanceUID = series_uid
    ds.SeriesNumber = series_number
    ds.SeriesDescription = description
    ds.Modality = modality
    ds.NumberOfSeriesRelatedInstances = "120"
    ds.BodyPartExamined = "CHEST"
    ds.ProtocolName = "CHEST_ROUTINE"
    ds.StationName = "CT_SCANNER_1"
    ds.Manufacturer = "GE MEDICAL SYSTEMS"
    ds.ManufacturerModelName = "Revolution CT"
    return ds


SAMPLE_STUDIES = [
    _make_study_dataset(),
    _make_study_dataset(
        patient_name="SMITH^JANE",
        patient_id="MRN002",
        accession="ACC002",
        study_date="20260402",
        modality="MR",
        description="MRI BRAIN W/WO CONTRAST",
        study_uid="1.2.840.113619.2.55.3.999.2",
    ),
]

SAMPLE_SERIES = [
    _make_series_dataset(),
    _make_series_dataset(
        series_uid="1.2.840.113619.2.55.3.999.1.2",
        modality="CT",
        description="CORONAL 3mm",
        series_number="3",
    ),
]


# ---------------------------------------------------------------
# Event handlers for the fake SCP
# ---------------------------------------------------------------

def _handle_echo(event: evt.Event) -> int:
    """Handle C-ECHO request."""
    return 0x0000  # Success


def _handle_find(event: evt.Event) -> Generator:
    """Handle C-FIND request."""
    ds = event.identifier
    query_level = getattr(ds, "QueryRetrieveLevel", "STUDY")

    if query_level == "SERIES":
        for series in SAMPLE_SERIES:
            yield 0xFF00, series  # Pending
    else:
        for study in SAMPLE_STUDIES:
            # Apply basic filtering
            if hasattr(ds, "PatientID") and ds.PatientID and ds.PatientID != study.PatientID:
                continue
            if hasattr(ds, "AccessionNumber") and ds.AccessionNumber and ds.AccessionNumber != study.AccessionNumber:
                continue
            if hasattr(ds, "StudyInstanceUID") and ds.StudyInstanceUID and ds.StudyInstanceUID != study.StudyInstanceUID:
                continue
            yield 0xFF00, study  # Pending


# ---------------------------------------------------------------
# Pytest fixture
# ---------------------------------------------------------------

@pytest.fixture(scope="session")
def fake_pacs_server():
    """Start a fake PACS SCP on localhost and return (host, port, ae_title).

    The server runs in a background thread and is shut down when the
    test session ends.
    """
    ae = AE(ae_title="FAKEPACS")
    ae.add_supported_context(Verification)
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)
    ae.add_supported_context(PatientRootQueryRetrieveInformationModelFind)

    handlers = [
        (evt.EVT_C_ECHO, _handle_echo),
        (evt.EVT_C_FIND, _handle_find),
    ]

    # Start on ephemeral port
    server = ae.start_server(("127.0.0.1", 0), evt_handlers=handlers, block=False)
    port = server.server_address[1]

    yield "127.0.0.1", port, "FAKEPACS"

    server.shutdown()
