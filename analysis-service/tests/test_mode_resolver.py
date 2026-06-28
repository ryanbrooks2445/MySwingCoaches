from app.mode_resolver import resolve_report_mode
from app.schemas import DiagnosticCheckpointGrade
from test_report_audit import _report as make_report


def test_forces_development_when_constraints_present() -> None:
    report = make_report()
    report.advanced_details.report_mode = "maintenance"
    resolved = resolve_report_mode(report)
    assert resolved.advanced_details.report_mode == "development"


def test_allows_maintenance_when_all_optimal() -> None:
    report = make_report()
    report.advanced_details.report_mode = "maintenance"
    report.advanced_details.diagnostic_checkpoints = [
        DiagnosticCheckpointGrade(checkpoint=f"Phase {i}", grade="optimal", observation="Strong")
        for i in range(6)
    ]
    resolved = resolve_report_mode(report)
    assert resolved.advanced_details.report_mode == "maintenance"
