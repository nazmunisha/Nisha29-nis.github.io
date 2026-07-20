# ==========================================================
#
# Purpose:
# This module generates attendance reports and summaries
# from the attendance records stored in the database.
#
# Features:
# • Monthly Attendance Report
# • Student Attendance Summary
#
# Technology Used:
# • Python
# • Pandas
# ==========================================================

# Import pandas library for data analysis and reporting
import pandas as pd


# ==========================================================
# Function: monthly_attendance_report()
#
# Purpose:
# Calculate the monthly attendance percentage for all students.
#
# Parameters:
# attendance_df - DataFrame containing attendance records.
#
# Process:
# 1. Check whether attendance data exists.
# 2. Convert attendance date into month format (YYYY-MM).
# 3. Group attendance records by month.
# 4. Count Present records.
# 5. Calculate monthly attendance percentage.
#
# Returns:
# A DataFrame containing:
# • Month
# • Attendance Percentage
# ==========================================================
def monthly_attendance_report(attendance_df):

    # Check if attendance data is empty
    # or the date column does not exist
    if attendance_df.empty or "date" not in attendance_df.columns:
        return pd.DataFrame()

    # Create a copy so the original data is not modified
    df = attendance_df.copy()

    # Convert the date column into Month-Year format
    # Example:
    # 2026-07-08  →  2026-07
    df["month"] = (
        pd.to_datetime(df["date"], errors="coerce")
        .dt.to_period("M")
        .astype(str)
    )

    # Group attendance records by month
    # Calculate percentage of Present attendance
    report = df.groupby("month")["status"].apply(
        lambda x:
        (
            x.astype(str).str.lower() == "present"
        ).sum() / len(x) * 100
    ).reset_index()

    # Rename column names
    report.columns = [
        "month",
        "attendance_percentage"
    ]

    # Return monthly attendance report
    return report


# ==========================================================
# Function: student_summary()
#
# Purpose:
# Generate attendance statistics for each student.
#
# Parameters:
# attendance_df - Attendance records
# students_df   - Student information
#
# Process:
# 1. Group attendance by student.
# 2. Count Present records.
# 3. Count Total attendance records.
# 4. Calculate attendance percentage.
# 5. Merge attendance statistics with student details.
#
# Returns:
# A DataFrame containing:
# • Student ID
# • Student Name
# • Present Count
# • Total Attendance
# • Attendance Percentage
# ==========================================================
def student_summary(attendance_df, students_df):

    # Check if attendance data is available
    if attendance_df.empty or not {
        "student_id",
        "status"
    }.issubset(attendance_df.columns):
        return pd.DataFrame()

    # Group attendance by student
    summary = attendance_df.groupby("student_id").agg(

        # Count number of Present records
        present=(
            "status",
            lambda x:
            (
                x.astype(str).str.lower() == "present"
            ).sum()
        ),

        # Count total attendance records
        total=(
            "status",
            "count"
        )

    ).reset_index()

    # Calculate attendance percentage
    summary["percentage"] = (
        summary["present"] /
        summary["total"].replace(0, 1)
        * 100
    ).round(2)

    # Merge attendance summary with student details
    if (
        not students_df.empty
        and "student_id" in students_df.columns
    ):

        summary = summary.merge(
            students_df,
            on="student_id",
            how="left"
        )

    # Return final student attendance summary
    return summary