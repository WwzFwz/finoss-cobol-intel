"""Contract tests for ImpactReport schema."""

from cobol_intel.contracts.impact_output import ImpactedEntity, ImpactReport, ImpactType


def test_impact_report_schema_version():
    report = ImpactReport()
    assert report.schema_version == "1.0"


def test_impact_report_serializes():
    entity = ImpactedEntity(
        program_id="ACCTVAL",
        file_path="acctval.cbl",
        impact_type=ImpactType.DIRECT_CALLER,
        distance=1,
        affected_paragraphs=["VALIDATE-ACCOUNT"],
        reason="Calls PAYMENT",
    )
    report = ImpactReport(
        changed_programs=["PAYMENT"],
        impacted_entities=[entity],
        total_impacted=1,
    )
    data = report.model_dump(mode="json")
    assert data["total_impacted"] == 1
    assert data["impacted_entities"][0]["impact_type"] == "direct_caller"


def test_all_impact_types_have_unique_values():
    values = [t.value for t in ImpactType]
    assert len(values) == len(set(values))
