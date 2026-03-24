"""Shared test fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def _clear_license_env(monkeypatch):
    """Ensure license key is not set during tests unless explicitly provided."""
    monkeypatch.delenv("DICOM_HL7_LICENSE_KEY", raising=False)


@pytest.fixture
def premium_enabled(monkeypatch):
    """Enable premium features for a test."""
    monkeypatch.setenv("DICOM_HL7_LICENSE_KEY", "test-license-key-12345678")


SAMPLE_ADT_A01 = (
    "MSH|^~\\&|ADT|HOSPITAL|PACS|HOSPITAL|20240315120000||ADT^A01^ADT_A01|MSG00001|P|2.5.1\r"
    "EVN|A01|20240315120000\r"
    "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^M||19650315|M|||123 MAIN ST^^ANYTOWN^NY^12345\r"
    "PV1|1|I|4EAST^401^A|E|||1234^ATTENDING^DOC^A^^DR|5678^REFERRING^DOC^B^^DR||MED||||1|||||||IP|VN001"
)

SAMPLE_ORM_O01 = (
    "MSH|^~\\&|CPOE|HOSPITAL|RIS|RAD|20240315130000||ORM^O01^ORM_O01|MSG00002|P|2.5.1\r"
    "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^M||19650315|M\r"
    "PV1|1|O|RAD|R|||1234^ATTENDING^DOC\r"
    "ORC|NW|ORD001^CPOE|ACC001^RIS||SC\r"
    "OBR|1|ORD001^CPOE|ACC001^RIS|CTABD^CT ABDOMEN WITH CONTRAST^L|||20240315130000||||||||Abdominal pain|||1234^ORDERING^DOC||||||RAD|SC"
)

SAMPLE_ORU_R01 = (
    "MSH|^~\\&|RIS|RAD|EMR|HOSPITAL|20240315140000||ORU^R01^ORU_R01|MSG00003|P|2.5.1\r"
    "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^M||19650315|M\r"
    "PV1|1|O|RAD\r"
    "ORC|RE|ORD001^CPOE|ACC001^RIS||CM\r"
    "OBR|1|ORD001^CPOE|ACC001^RIS|CTABD^CT ABDOMEN WITH CONTRAST^L|||20240315130000||||||||Abdominal pain|||1234^ORDERING^DOC||||||RAD|F||||||5555^READING^RAD^^DR\r"
    "OBX|1|FT|&GDT^Radiology Report^L||FINDINGS: Normal CT abdomen.||||||F\r"
    "OBX|2|FT|&IMP^Impression^L||IMPRESSION: No acute findings.||||||F"
)

SAMPLE_MALFORMED = "PID|1||MRN12345|||DOE^JOHN"

SAMPLE_EMPTY = ""
