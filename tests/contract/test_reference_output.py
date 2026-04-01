"""Contract tests for ReferenceIndex schema."""

from cobol_intel.contracts.reference_output import (
    FieldReference,
    ReferenceIndex,
    ReferenceType,
)


def test_reference_index_schema_version():
    idx = ReferenceIndex(program_id="TEST")
    assert idx.schema_version == "1.0"


def test_reference_type_values():
    assert ReferenceType.READ.value == "read"
    assert ReferenceType.WRITE.value == "write"
    assert ReferenceType.CONDITION.value == "condition"
    assert ReferenceType.CALL_PARAM.value == "call_param"


def test_field_reference_construction():
    ref = FieldReference(
        field_name="WS-BALANCE",
        reference_type=ReferenceType.WRITE,
        paragraph="MAIN",
        statement_type="MOVE",
        statement_raw="MOVE 0 TO WS-BALANCE",
    )
    assert ref.field_name == "WS-BALANCE"
    assert ref.reference_type == ReferenceType.WRITE


def test_reference_index_roundtrip():
    idx = ReferenceIndex(
        program_id="PAYMENT",
        file_path="payment.cbl",
        references=[
            FieldReference(
                field_name="WS-AMOUNT",
                reference_type=ReferenceType.READ,
                paragraph="CALC",
                statement_type="COMPUTE",
            ),
        ],
        field_read_count={"WS-AMOUNT": 3},
        field_write_count={"WS-TOTAL": 1},
        defined_fields=["WS-AMOUNT", "WS-TOTAL"],
        entry_fields=["WS-INPUT"],
        unsupported_constructs=["GO TO"],
    )
    data = idx.model_dump()
    restored = ReferenceIndex.model_validate(data)
    assert restored.program_id == "PAYMENT"
    assert len(restored.references) == 1
    assert restored.field_read_count["WS-AMOUNT"] == 3
    assert restored.entry_fields == ["WS-INPUT"]
