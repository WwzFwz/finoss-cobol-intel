"""Contract tests for ExplanationOutput schema."""

from cobol_intel.contracts.explanation_output import (
    ExplanationMode,
    ExplanationOutput,
    ParagraphExplanation,
)
from cobol_intel.contracts.source_ref import SourceRef


def test_explanation_output_schema_version():
    exp = ExplanationOutput(program_id="HELLO")
    assert exp.schema_version == "1.0"


def test_explanation_output_serializes_with_required_fields():
    exp = ExplanationOutput(
        program_id="CALC",
        mode=ExplanationMode.BUSINESS,
        backend="claude",
        model="claude-sonnet-4-20250514",
        program_summary="A calculator program.",
    )
    data = exp.model_dump()
    required = {
        "schema_version", "program_id", "file_path", "mode", "backend",
        "model", "program_summary", "paragraph_explanations",
        "program_summary_sources", "data_summary", "data_summary_sources",
        "business_rules_summary", "business_rules_summary_sources",
        "paragraph_limit", "paragraphs_skipped", "tokens_used",
    }
    assert required.issubset(data.keys())


def test_explanation_mode_values():
    assert ExplanationMode.TECHNICAL.value == "technical"
    assert ExplanationMode.BUSINESS.value == "business"
    assert ExplanationMode.AUDIT.value == "audit"


def test_paragraph_explanation_with_source_ref():
    para = ParagraphExplanation(
        paragraph="MAIN-PROGRAM",
        summary="Entry point that validates input and processes payment.",
        source=SourceRef(file="PAYMENT.cbl", paragraph="MAIN-PROGRAM"),
    )
    data = para.model_dump()
    assert data["paragraph"] == "MAIN-PROGRAM"
    assert data["source"]["file"] == "PAYMENT.cbl"
    assert data["source"]["paragraph"] == "MAIN-PROGRAM"


def test_explanation_output_with_paragraphs():
    exp = ExplanationOutput(
        program_id="TEST",
        paragraph_explanations=[
            ParagraphExplanation(paragraph="INIT", summary="Initializes variables."),
            ParagraphExplanation(paragraph="PROCESS", summary="Processes data."),
        ],
        tokens_used=1500,
    )
    data = exp.model_dump()
    assert len(data["paragraph_explanations"]) == 2
    assert data["tokens_used"] == 1500


def test_explanation_output_top_level_traceability_fields():
    exp = ExplanationOutput(
        program_summary_sources=[SourceRef(file="PAYMENT.cbl", paragraph="MAIN-PROGRAM")],
        data_summary_sources=[SourceRef(file="PAYMENT.cbl")],
        business_rules_summary_sources=[SourceRef(file="PAYMENT.cbl", paragraph="VALIDATE")],
        paragraph_limit=8,
        paragraphs_skipped=["LOGGING-PARA"],
    )
    data = exp.model_dump()
    assert data["program_summary_sources"][0]["paragraph"] == "MAIN-PROGRAM"
    assert data["data_summary_sources"][0]["file"] == "PAYMENT.cbl"
    assert data["business_rules_summary_sources"][0]["paragraph"] == "VALIDATE"
    assert data["paragraph_limit"] == 8
    assert data["paragraphs_skipped"] == ["LOGGING-PARA"]
