"""Education Intelligence — Student performance, attendance, fees, teacher analytics.

Specialized analytics for schools, universities, and educational institutions:
  - Student enrollment and demographics
  - Academic performance (grades, pass rates, GPA)
  - Attendance patterns
  - Fee collection and revenue
  - Teacher workload and performance
"""

from __future__ import annotations

import pandas as pd

from industry_intelligence.base import (
    AnalyticsResult,
    Breakdown,
    IndustryAnalytics,
    IndustryAnalyticsRegistry,
    Insight,
    Trend,
)


class EducationAnalytics(IndustryAnalytics):
    industry = "education"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        student_col = cls._find_col(df, col_mapping, ["student"])
        teacher_col = cls._find_col(df, col_mapping, ["teacher"])
        course_col = cls._find_col(df, col_mapping, ["course"])
        dept_col = cls._find_col(df, col_mapping, ["department_edu", "department"])
        grade_col = cls._find_col(df, col_mapping, ["grade"])
        attendance_col = cls._find_col(df, col_mapping, ["attendance"])
        fee_col = cls._find_numeric_col(df, col_mapping, ["revenue", "fees"])
        date_col = cls._find_date_col(df, col_mapping)
        exam_col = cls._find_col(df, col_mapping, ["exam"])

        # ── Student Analytics ────────────────────────────
        if student_col and student_col in df.columns:
            student_count = int(df[student_col].nunique())
            insights.append(Insight(
                title="Total Students",
                value=student_count,
                formatted=cls._fmt_number(student_count),
                category="operational",
                description=f"Unique students enrolled.",
            ))

        # ── Academic Performance ─────────────────────────
        if grade_col and grade_col in df.columns:
            grade_count = int(df[grade_col].nunique())
            insights.append(Insight(
                title="Grade Records",
                value=grade_count,
                formatted=cls._fmt_number(grade_count),
                category="academic",
                description="Distinct grade entries recorded.",
            ))

            # Grade distribution
            grade_bd = cls._compute_breakdown(df, grade_col, grade_col, "count")
            if grade_bd:
                grade_bd.dimension = "Grade"
                grade_bd.metric = "count"
                breakdowns.append(grade_bd)

                # Check for high failure rate
                fail_grades = [g for g in grade_bd.values if any(
                    fg in str(g).upper() for fg in ("F", "FAIL", "0", "1")
                )]
                if fail_grades:
                    fail_count = sum(grade_bd.values.get(fg, 0) for fg in grade_bd.values
                                     if any(f in str(fg).upper() for f in ("F", "FAIL")))
                    if fail_count > 0:
                        total = sum(grade_bd.values.values())
                        fail_rate = (fail_count / total * 100) if total > 0 else 0
                        insights.append(Insight(
                            title="Failure Rate",
                            value=fail_rate,
                            formatted=cls._fmt_pct(fail_rate),
                            category="academic",
                            description="Percentage of failing grades.",
                            alert="critical" if fail_rate > 20 else "warning" if fail_rate > 10 else "ok",
                        ))

            # Numeric grade average (GPA-like)
            if pd.api.types.is_numeric_dtype(df[grade_col]):
                avg_grade = float(df[grade_col].dropna().mean())
                insights.append(Insight(
                    title="Average Grade",
                    value=avg_grade,
                    formatted=f"{avg_grade:.2f}",
                    category="academic",
                    description="Mean numeric grade across all records.",
                ))

        # ── Attendance ───────────────────────────────────
        if attendance_col and attendance_col in df.columns:
            if pd.api.types.is_numeric_dtype(df[attendance_col]):
                avg_attendance = float(df[attendance_col].dropna().mean())
                insights.append(Insight(
                    title="Average Attendance",
                    value=avg_attendance,
                    formatted=cls._fmt_pct(avg_attendance) if avg_attendance <= 100 else cls._fmt_number(avg_attendance),
                    category="academic",
                    description="Mean attendance rate across records.",
                    alert="warning" if avg_attendance < 75 else "ok",
                ))
            else:
                att_count = int(df[attendance_col].nunique())
                insights.append(Insight(
                    title="Attendance Records",
                    value=att_count,
                    formatted=cls._fmt_number(att_count),
                    category="academic",
                    description="Distinct attendance entries.",
                ))

        # ── Fee Collection ───────────────────────────────
        if fee_col and fee_col in df.columns:
            total_fees = float(df[fee_col].sum())
            insights.append(Insight(
                title="Total Fees",
                value=total_fees,
                formatted=cls._fmt_currency(total_fees),
                category="financial",
                description="Total fee/sales amount recorded.",
            ))

            if student_col and student_col in df.columns:
                student_count = max(int(df[student_col].nunique()), 1)
                avg_fee = total_fees / student_count
                insights.append(Insight(
                    title="Avg Fee per Student",
                    value=avg_fee,
                    formatted=cls._fmt_currency(avg_fee),
                    category="financial",
                    description="Average fee amount per student.",
                ))

            # Fee trend
            if date_col:
                fee_trend = cls._compute_trend(df, date_col, fee_col, "sum")
                if fee_trend:
                    fee_trend.metric = "fees"
                    trends.append(fee_trend)

        # ── Teacher Analytics ────────────────────────────
        if teacher_col and teacher_col in df.columns:
            teacher_count = int(df[teacher_col].nunique())
            insights.append(Insight(
                title="Active Teachers",
                value=teacher_count,
                formatted=cls._fmt_number(teacher_count),
                category="operational",
                description="Unique teachers in the dataset.",
            ))

            if student_col and student_col in df.columns and teacher_count > 0:
                teacher_bd = cls._compute_breakdown(df, teacher_col, student_col, "count")
                if teacher_bd:
                    teacher_bd.dimension = "Teacher"
                    teacher_bd.metric = "students"
                    breakdowns.append(teacher_bd)

                    avg_students = sum(teacher_bd.values.values()) / len(teacher_bd.values)
                    insights.append(Insight(
                        title="Avg Students per Teacher",
                        value=avg_students,
                        formatted=cls._fmt_number(avg_students),
                        category="operational",
                        description="Average student load per teacher.",
                        alert="warning" if avg_students > 40 else "ok",
                    ))

        # ── Course Analytics ─────────────────────────────
        if course_col and course_col in df.columns:
            course_count = int(df[course_col].nunique())
            insights.append(Insight(
                title="Active Courses",
                value=course_count,
                formatted=cls._fmt_number(course_count),
                category="academic",
                description="Distinct courses offered.",
            ))

            if student_col and student_col in df.columns:
                course_bd = cls._compute_breakdown(df, course_col, student_col, "count")
                if course_bd:
                    course_bd.dimension = "Course"
                    course_bd.metric = "students"
                    breakdowns.append(course_bd)

        # ── Department Analytics ─────────────────────────
        if dept_col and dept_col in df.columns:
            dept_count = int(df[dept_col].nunique())
            insights.append(Insight(
                title="Departments",
                value=dept_count,
                formatted=cls._fmt_number(dept_count),
                category="operational",
                description="Number of distinct departments.",
            ))

            if student_col and student_col in df.columns:
                dept_bd = cls._compute_breakdown(df, dept_col, student_col, "count")
                if dept_bd:
                    dept_bd.dimension = "Department"
                    dept_bd.metric = "students"
                    breakdowns.append(dept_bd)

        recommendations.extend([
            "Monitor student attendance for early intervention.",
            "Track grade distribution by course to identify curriculum gaps.",
            "Review teacher workload distribution for balanced assignments.",
            "Analyze fee collection trends to improve revenue forecasting.",
        ])

        for insight in insights:
            if insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} — needs attention.")
            elif insight.alert == "critical":
                alerts.append(f"CRITICAL: {insight.title}: {insight.formatted} — immediate action required.")

        return AnalyticsResult(
            industry="education",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("education", EducationAnalytics)
