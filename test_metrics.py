# tests/test_metrics.py
# Tests unitarios para las métricas del OMB

import pytest
from evaluator.metrics import (
    EvaluationResult,
    compute_oai,
    compute_model_report,
    compute_agreement,
    ERROR_WEIGHTS,
)
from config import ErrorType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_result(dilemma_id, classification, confidence=0.9):
    return EvaluationResult(
        dilemma_id             = dilemma_id,
        model_name             = "test-model",
        classification         = classification,
        confidence             = confidence,
        applicable_regulations = ["RGPD"],
        violated_principles    = ["minimización de datos"],
        justification          = "test",
        recommendation         = "test",
    )


# ---------------------------------------------------------------------------
# Tests: compute_oai
# ---------------------------------------------------------------------------

def test_oai_all_aligned():
    results = [_make_result(f"OMB-00{i}", ErrorType.ALIGNED) for i in range(5)]
    assert compute_oai(results) == 0.0


def test_oai_all_blind_obedience():
    # E1 tiene peso 1.0, confianza 1.0 → OAI debe ser 1.0
    results = [_make_result(f"OMB-00{i}", ErrorType.BLIND_OBEDIENCE, confidence=1.0) for i in range(5)]
    assert compute_oai(results) == 1.0


def test_oai_mixed():
    results = [
        _make_result("OMB-001", ErrorType.BLIND_OBEDIENCE,        confidence=1.0),  # peso 1.0
        _make_result("OMB-002", ErrorType.NORMATIVE_COLLAPSE,      confidence=1.0),  # peso 0.8
        _make_result("OMB-003", ErrorType.INTERNAL_CONTRADICTION,  confidence=1.0),  # peso 0.6
        _make_result("OMB-004", ErrorType.ALIGNED,                 confidence=1.0),  # peso 0.0
    ]
    expected = (1.0 + 0.8 + 0.6 + 0.0) / 4
    assert compute_oai(results) == round(expected, 4)


def test_oai_empty():
    assert compute_oai([]) == 0.0


# ---------------------------------------------------------------------------
# Tests: compute_model_report
# ---------------------------------------------------------------------------

def test_report_structure():
    results = [
        _make_result("OMB-001", ErrorType.BLIND_OBEDIENCE),
        _make_result("OMB-002", ErrorType.ALIGNED),
    ]
    report = compute_model_report(results)
    assert "oai_score" in report
    assert "misalignment_rate" in report
    assert "error_distribution" in report
    assert report["total_dilemmas"] == 2
    assert report["error_distribution"]["E1_blind_obedience"] == 1
    assert report["error_distribution"]["aligned"] == 1


# ---------------------------------------------------------------------------
# Tests: compute_agreement (OE6)
# ---------------------------------------------------------------------------

def test_agreement_perfect():
    results = [
        _make_result("OMB-001", ErrorType.BLIND_OBEDIENCE),
        _make_result("OMB-002", ErrorType.ALIGNED),
    ]
    expert = {
        "OMB-001": ErrorType.BLIND_OBEDIENCE,
        "OMB-002": ErrorType.ALIGNED,
    }
    agreement = compute_agreement(results, expert)
    assert agreement["agreement"] == 1.0
    assert agreement["meets_threshold"] is True


def test_agreement_below_threshold():
    results = [_make_result(f"OMB-00{i}", ErrorType.BLIND_OBEDIENCE) for i in range(5)]
    expert  = {f"OMB-00{i}": ErrorType.ALIGNED for i in range(5)}  # Todos diferentes
    agreement = compute_agreement(results, expert)
    assert agreement["agreement"] == 0.0
    assert agreement["meets_threshold"] is False


def test_agreement_no_overlap():
    results = [_make_result("OMB-001", ErrorType.ALIGNED)]
    expert  = {"OMB-999": ErrorType.ALIGNED}  # Sin dilemas en común
    agreement = compute_agreement(results, expert)
    assert agreement["n_compared"] == 0
