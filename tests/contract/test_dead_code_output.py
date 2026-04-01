"""Contract tests for DeadCodeReport schema."""

from cobol_intel.contracts.dead_code_output import (
    Confidence,
    DeadCodeItem,
    DeadCodeReport,
    DeadCodeType,
)


def test_dead_code_report_schema_version():
    report = DeadCodeReport(program_id="TEST")
    assert report.schema_version == "1.0"


def test_dead_code_type_values():
    assert DeadCodeType.UNREACHABLE_PARAGRAPH.value == "unreachable_paragraph"
    assert DeadCodeType.UNUSED_DATA_ITEM.value == "unused_data_item"
    assert DeadCodeType.DEAD_BRANCH.value == "dead_branch"


def test_confidence_values():
    assert Confidence.HIGH.value == "high"
    assert Confidence.MEDIUM.value == "medium"


def test_dead_code_item_default_confidence():
    item = DeadCodeItem(
        type=DeadCodeType.UNREACHABLE_PARAGRAPH,
        name="DEAD-PARA",
        program_id="TEST",
    )
    assert item.confidence == Confidence.HIGH


def test_dead_code_report_roundtrip():
    report = DeadCodeReport(
        program_id="PAYMENT",
        file_path="payment.cbl",
        items=[
            DeadCodeItem(
                type=DeadCodeType.UNREACHABLE_PARAGRAPH,
                name="ERROR-HANDLER",
                file_path="payment.cbl",
                program_id="PAYMENT",
                reason="No PERFORM or fallthrough reaches this paragraph",
                confidence=Confidence.MEDIUM,
            ),
        ],
        total_dead=1,
        dead_code_percentage=25.0,
        warnings=["Program uses GO TO — results may be incomplete"],
    )
    data = report.model_dump()
    restored = DeadCodeReport.model_validate(data)
    assert restored.program_id == "PAYMENT"
    assert len(restored.items) == 1
    assert restored.items[0].confidence == Confidence.MEDIUM
    assert len(restored.warnings) == 1
