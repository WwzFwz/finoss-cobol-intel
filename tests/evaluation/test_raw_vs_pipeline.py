"""Evaluation test: raw LLM vs pipeline+LLM.

Compares LLM explanation quality when given:
  A) Raw COBOL source directly (no preprocessing)
  B) Phase 1 artifacts (AST + rules + graph) via context builder

This test uses a mock backend to verify the pipeline produces
richer, more structured prompts. Real evaluation with live LLMs
should be run manually with: pytest tests/evaluation/ -m live

See ADR-010 (testing strategy) — evaluation tests compare raw vs pipeline.
"""

from pathlib import Path

import pytest

from cobol_intel.contracts.explanation_output import ExplanationMode
from cobol_intel.llm.backend import LLMBackend, LLMResponse
from cobol_intel.llm.context_builder import build_program_prompt, build_system_prompt
from cobol_intel.llm.explainer import explain_program
from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor
from cobol_intel.analysis.rules_extractor import extract_rules
from cobol_intel.service.pipeline import to_ast_output

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"


class RecordingBackend(LLMBackend):
    """Records prompts sent to the backend for comparison."""

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.system_prompts: list[str] = []

    @property
    def name(self) -> str:
        return "recording"

    @property
    def model_id(self) -> str:
        return "recording-v1"

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        self.prompts.append(prompt)
        self.system_prompts.append(system)
        return LLMResponse(text="Mock explanation.", model="recording-v1",
                           input_tokens=len(prompt) // 4, output_tokens=20)


class TestRawVsPipelinePrompts:
    """Compare what the LLM would receive in raw vs pipeline mode."""

    @pytest.fixture
    def payment_source(self):
        path = SAMPLES_DIR / "complex" / "payment.cbl"
        return path.read_text(encoding="utf-8"), str(path)

    @pytest.fixture
    def pipeline_artifacts(self, payment_source):
        source, file_path = payment_source
        pp = COBOLPreprocessor()
        preprocessed = pp.preprocess(source, file_path=file_path)
        parser = ANTLR4Parser()
        result = parser.parse(preprocessed.text, file_path=file_path)
        assert result.success
        ast = to_ast_output(result, file_path=file_path)
        rules = extract_rules(result, file_path=file_path)
        return ast, rules

    def test_pipeline_prompt_is_more_structured(self, payment_source, pipeline_artifacts):
        """Pipeline prompt should contain structured sections not in raw source."""
        raw_source, _ = payment_source
        ast, rules = pipeline_artifacts

        pipeline_prompt = build_program_prompt(ast, rules=rules)

        # Pipeline prompt has structured sections
        assert "## Data Items" in pipeline_prompt
        assert "## Paragraphs" in pipeline_prompt
        assert "## Extracted Business Rules" in pipeline_prompt

        # Raw source does NOT have these structures
        assert "## Data Items" not in raw_source
        assert "## Paragraphs" not in raw_source

    def test_pipeline_prompt_contains_extracted_rules(self, pipeline_artifacts):
        """Pipeline prompt should include business rules that raw source doesn't surface."""
        ast, rules = pipeline_artifacts
        prompt = build_program_prompt(ast, rules=rules)

        # Should contain rule IDs
        assert "R001" in prompt or "R00" in prompt
        # Should contain IF or EVALUATE rule types
        assert "IF" in prompt

    def test_pipeline_prompt_has_hierarchical_data(self, pipeline_artifacts):
        """Pipeline prompt should show data hierarchy, not raw COBOL layout."""
        ast, _ = pipeline_artifacts
        prompt = build_program_prompt(ast)

        # Should show COMP-3 usage extracted from data items
        assert "COMP-3" in prompt
        # Should show condition values
        assert "88" in prompt or "STATUS-OK" in prompt or "CURRENCY" in prompt

    def test_explainer_tracks_token_usage(self, pipeline_artifacts):
        """Explainer should report tokens used for cost tracking."""
        ast, rules = pipeline_artifacts
        backend = RecordingBackend()
        result = explain_program(backend, ast, rules=rules)

        assert result.tokens_used > 0
        assert len(backend.prompts) > 1  # summary + paragraphs

    def test_system_prompt_varies_by_mode(self):
        """Each mode should produce a different system prompt."""
        prompts = {
            mode: build_system_prompt(mode) for mode in ExplanationMode
        }
        # All different
        assert len(set(prompts.values())) == 3
