from __future__ import annotations

from app.schemas import CoachingReportSchema


def resolve_report_mode(report: CoachingReportSchema) -> CoachingReportSchema:
    """
    Server-side mode resolver: maintenance only when checkpoint grades support it.
    Overrides Gemini when maintenance contradicts visible constraint grades.
    """
    adv = report.advanced_details
    checkpoints = adv.diagnostic_checkpoints

    if not checkpoints:
        return report

    optimal_count = 0
    constraint_count = 0
    compensation_count = 0

    for item in checkpoints:
        grade = (item.grade or "").lower()
        if grade == "optimal":
            optimal_count += 1
        elif grade == "constraint":
            constraint_count += 1
        elif grade == "compensation":
            compensation_count += 1

    visible_issues = constraint_count + compensation_count
    should_be_maintenance = (
        optimal_count >= 5
        and constraint_count == 0
        and visible_issues == 0
    )

    if adv.report_mode == "maintenance" and not should_be_maintenance:
        adv.report_mode = "development"
    elif adv.report_mode == "development" and should_be_maintenance and compensation_count == 0:
        adv.report_mode = "maintenance"

    report.advanced_details = adv
    return report
