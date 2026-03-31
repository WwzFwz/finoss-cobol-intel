"""Contract tests for rules output schema."""

from cobol_intel.contracts.rules_output import BusinessRule, RulesOutput
from cobol_intel.contracts.source_ref import SourceRef


def test_rules_output_schema_version():
    rules = RulesOutput(program_id="PAYMENT")
    assert rules.schema_version == "1.0"


def test_rules_output_serializes_required_fields():
    output = RulesOutput(
        program_id="PAYMENT",
        file_path="samples/complex/payment.cbl",
        rules=[
            BusinessRule(
                rule_id="R001",
                type="IF",
                condition="STATUS-OK",
                actions=["PERFORM"],
            )
        ],
    )
    data = output.model_dump()
    required = {"schema_version", "program_id", "file_path", "rules"}
    assert required.issubset(data.keys())


def test_business_rule_keeps_source_ref():
    output = RulesOutput(
        rules=[
            BusinessRule(
                rule_id="R001",
                type="IF",
                condition="STATUS-OK",
                source=SourceRef(file="PAYMENT.cbl", paragraph="MAIN-PROGRAM"),
            )
        ]
    )
    data = output.model_dump()
    assert data["rules"][0]["source"]["file"] == "PAYMENT.cbl"
