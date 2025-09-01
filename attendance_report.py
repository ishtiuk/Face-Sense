import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse
import sys

def fancy_banner():
    banner = f"""
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█░▄▄▀██░▄▄▄██░▄▄▄░██░▄▄▀██░▄▄▄██░▄▄▄░██░▄▄▄░██░▄▄▄░██░▄▄▄██░▄▄▀██░▄▄▄██░▄▄▄░██
█░▀▀▄██░▄▄▄██▄▄▄▀▀██░▀▀▄██░▄▄▄██░███░██▄▄▄▀▀██▄▄▄▀▀██░▄▄▄██░▀▀▄██░▄▄▄██░███░██
█░██░██░▀▀▀██░▀▀▀░██░██░██░▀▀▀██░▀▀▀░██░▀▀▀░██░▀▀▀░██░▀▀▀██░██░██░▀▀▀██░▀▀▀░██
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
Office Attendance System - Reporting Tool\n\n"""
    print(banner)

class AttendanceReport:
    def __init__(self, db_path="attendance_data/attendance.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Ensure output directory exists
        os.makedirs("attendance_reports", exist_ok=True)
        
    def connect_db(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"[!] Database connection error: {e}")
            return False
            
    def close_db(self):
        if self.conn:
            self.conn.close()
            
    def get_table_for_date(self, date_str=None):
        """Get the table name for a specific date or today"""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        table_name = "t_" + date_str.replace("-", "_")
        return table_name
        
    def get_all_tables(self):
        """Get all attendance tables in the database"""
        self.connect_db()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 't_%'")
        tables = [row[0] for row in self.cursor.fetchall()]
        self.close_db()
        return tables
        
    def get_date_from_table(self, table_name):
        """Convert table name to date string"""
        if table_name.startswith("t_"):
            date_parts = table_name[2:].split("_")
            if len(date_parts) == 3:
                return f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
        return None
        
    def get_daily_report(self, date_str=None):
        """Generate daily attendance report for a specific date"""
        table_name = self.get_table_for_date(date_str)
        
        if not self.connect_db():
            return None
            
        # Check if table exists
        self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not self.cursor.fetchone():
            print(f"[!] No attendance data found for {date_str}")
            self.close_db()
            return None
            
        # Get attendance data
        self.cursor.execute(f"""
            SELECT employee_name, employee_id, time_in, time_out, status
            FROM {table_name}
            ORDER BY employee_name
        """)
        
        rows = self.cursor.fetchall()
        self.close_db()
        
        if not rows:
            print(f"[!] No attendance records found for {date_str}")
            return None
            
        # Create DataFrame
        df = pd.DataFrame(rows, columns=['Employee Name', 'Employee ID', 'Time In', 'Time Out', 'Status'])
        
        # Calculate work hours for employees who have both in and out times
        df['Work Hours'] = None
        
        for idx, row in df.iterrows():
            if row['Time In'] and row['Time Out']:
                try:
                    time_in = datetime.strptime(row['Time In'], "%I:%M:%S %p")
                    time_out = datetime.strptime(row['Time Out'], "%I:%M:%S %p")
                    
                    # Handle case where checkout is next day (should not happen in normal office hours)
                    if time_out < time_in:
                        time_out += timedelta(days=1)
                        
                    delta = time_out - time_in
                    hours = delta.total_seconds() / 3600
                    df.at[idx, 'Work Hours'] = round(hours, 2)
                except Exception as e:
                    print(f"[!] Error calculating work hours: {e}")
        
        # Add date to the DataFrame for reference
        date_display = date_str if date_str else datetime.now().strftime("%Y-%m-%d")
        df['Date'] = date_display
        
        return df
        
    def generate_weekly_report(self, end_date=None):
        """Generate weekly attendance report ending on specified date"""
        if not end_date:
            end_date = datetime.now().date()
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
        start_date = end_date - timedelta(days=6)  # 7 days including end_date
        
        print(f"[+] Generating weekly report from {start_date} to {end_date}")
        
        # Get all tables
        all_tables = self.get_all_tables()
        
        # Filter tables for the week
        weekly_dfs = []
        
        for table in all_tables:
            table_date_str = self.get_date_from_table(table)
            if not table_date_str:
                continue
                
            table_date = datetime.strptime(table_date_str, "%Y-%m-%d").date()
            
            if start_date <= table_date <= end_date:
                daily_df = self.get_daily_report(table_date_str)
                if daily_df is not None:
                    weekly_dfs.append(daily_df)
        
        if not weekly_dfs:
            print(f"[!] No attendance data found for the week {start_date} to {end_date}")
            return None
            
        # Combine all daily reports
        weekly_df = pd.concat(weekly_dfs)
        
        # Save to Excel
        report_file = f"attendance_reports/weekly_report_{start_date}_to_{end_date}.xlsx"
        weekly_df.to_excel(report_file, index=False)
        
        print(f"[+] Weekly report saved to {report_file}")
        
        # Generate summary statistics
        self._generate_weekly_summary(weekly_df, start_date, end_date)
        
        return weekly_df
        
    def _generate_weekly_summary(self, df, start_date, end_date):
        """Generate summary statistics and charts for weekly report"""
        # Count attendance by date
        attendance_by_date = df.groupby('Date').size()
        
        # Group by employee ID for better reporting
        attendance_by_employee = df.groupby('Employee ID').size()
        
        # Calculate average work hours
        avg_work_hours = df['Work Hours'].mean()
        
        # Count employees who worked full day (>= 8 hours)
        full_day_count = df[df['Work Hours'] >= 8].shape[0]
        
        # Create a summary DataFrame
        summary = pd.DataFrame({
            'Start Date': [start_date],
            'End Date': [end_date],
            'Total Attendance Records': [df.shape[0]],
            'Average Work Hours': [round(avg_work_hours, 2) if not pd.isna(avg_work_hours) else 0],
            'Full Day Count': [full_day_count],
            'Unique Employees': [len(df['Employee ID'].unique())]
        })
        
        # Save summary to Excel
        summary_file = f"attendance_reports/weekly_summary_{start_date}_to_{end_date}.xlsx"
        summary.to_excel(summary_file, index=False)
        
        print(f"[+] Weekly summary saved to {summary_file}")
        
        # Generate charts
        plt.figure(figsize=(15, 10))
        
        # Attendance by date chart
        plt.subplot(2, 2, 1)
        attendance_by_date.plot(kind='bar', color='skyblue')
        plt.title('Daily Attendance Count')
        plt.xlabel('Date')
        plt.ylabel('Number of Employees')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Attendance by employee ID chart
        plt.subplot(2, 2, 2)
        attendance_by_employee.plot(kind='bar', color='lightgreen')
        plt.title('Attendance by Employee ID')
        plt.xlabel('Employee ID')
        plt.ylabel('Attendance Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Work hours distribution
        plt.subplot(2, 2, 3)
        df['Work Hours'].dropna().plot(kind='hist', bins=10, color='lightgreen')
        plt.title('Work Hours Distribution')
        plt.xlabel('Hours')
        plt.ylabel('Frequency')
        plt.tight_layout()
        
        # Employee work hours by ID
        plt.subplot(2, 2, 4)
        if 'Employee ID' in df.columns and 'Work Hours' in df.columns:
            employee_hours = df.groupby('Employee ID')['Work Hours'].sum().sort_values(ascending=False)
            employee_hours.plot(kind='bar', color='salmon')
            plt.title('Total Work Hours by Employee ID')
            plt.xlabel('Employee ID')
            plt.ylabel('Total Hours')
            plt.xticks(rotation=45)
            plt.tight_layout()
        
        # Save chart
        chart_file = f"attendance_reports/weekly_chart_{start_date}_to_{end_date}.png"
        plt.savefig(chart_file)
        
        print(f"[+] Weekly chart saved to {chart_file}")
        
    def generate_monthly_report(self, month=None, year=None):
        """Generate monthly attendance report"""
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
            
        # Get first and last day of month
        first_day = datetime(year, month, 1).date()
        
        # Get last day by getting first day of next month and subtracting 1 day
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
        print(f"[+] Generating monthly report for {first_day.strftime('%B %Y')}")
        
        # Get all tables
        all_tables = self.get_all_tables()
        
        # Filter tables for the month
        monthly_dfs = []
        
        for table in all_tables:
            table_date_str = self.get_date_from_table(table)
            if not table_date_str:
                continue
                
            table_date = datetime.strptime(table_date_str, "%Y-%m-%d").date()
            
            if first_day <= table_date <= last_day:
                daily_df = self.get_daily_report(table_date_str)
                if daily_df is not None:
                    monthly_dfs.append(daily_df)
        
        if not monthly_dfs:
            print(f"[!] No attendance data found for {first_day.strftime('%B %Y')}")
            return None
            
        # Combine all daily reports
        monthly_df = pd.concat(monthly_dfs)
        
        # Save to Excel
        month_name = first_day.strftime('%B')
        report_file = f"attendance_reports/monthly_report_{month_name}_{year}.xlsx"
        monthly_df.to_excel(report_file, index=False)
        
        print(f"[+] Monthly report saved to {report_file}")
        
        # Generate employee summary
        self._generate_employee_summary(monthly_df, month_name, year)
        
        return monthly_df
        
    def _generate_employee_summary(self, df, month_name, year):
        """Generate employee-wise summary for monthly report"""
        # Group by employee
        employee_summary = df.groupby(['Employee Name', 'Employee ID']).agg({
            'Date': 'nunique',  # Count unique dates (days present)
            'Work Hours': 'sum'  # Total work hours
        }).reset_index()
        
        # Rename columns
        employee_summary.columns = ['Employee Name', 'Employee ID', 'Days Present', 'Total Work Hours']
        
        # Calculate average hours per day
        employee_summary['Avg Hours/Day'] = employee_summary['Total Work Hours'] / employee_summary['Days Present']
        employee_summary['Avg Hours/Day'] = employee_summary['Avg Hours/Day'].round(2)
        
        # Save to Excel
        summary_file = f"attendance_reports/employee_summary_{month_name}_{year}.xlsx"
        employee_summary.to_excel(summary_file, index=False)
        
        print(f"[+] Employee summary saved to {summary_file}")
        
        # Generate charts
        plt.figure(figsize=(15, 10))
        
        # Days present chart
        plt.subplot(2, 1, 1)
        employee_summary.sort_values('Days Present', ascending=False).head(10).plot(
            x='Employee Name', 
            y='Days Present', 
            kind='bar',
            color='skyblue'
        )
        plt.title('Top 10 Employees by Attendance')
        plt.xlabel('Employee')
        plt.ylabel('Days Present')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Work hours chart
        plt.subplot(2, 1, 2)
        employee_summary.sort_values('Total Work Hours', ascending=False).head(10).plot(
            x='Employee Name', 
            y='Total Work Hours', 
            kind='bar',
            color='lightgreen'
        )
        plt.title('Top 10 Employees by Work Hours')
        plt.xlabel('Employee')
        plt.ylabel('Total Hours')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart
        chart_file = f"attendance_reports/employee_chart_{month_name}_{year}.png"
        plt.savefig(chart_file)
        
        print(f"[+] Employee chart saved to {chart_file}")

def main():
    fancy_banner()
    
    parser = argparse.ArgumentParser(description='Office Attendance Reporting Tool')
    parser.add_argument('--daily', action='store_true', help='Generate daily report')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--monthly', action='store_true', help='Generate monthly report')
    parser.add_argument('--date', type=str, help='Date for daily report (YYYY-MM-DD)')
    parser.add_argument('--month', type=int, help='Month number for monthly report (1-12)')
    parser.add_argument('--year', type=int, help='Year for monthly report')
    
    args = parser.parse_args()
    
    report = AttendanceReport()
    
    if args.daily:
        df = report.get_daily_report(args.date)
        if df is not None:
            date_str = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
            report_file = f"attendance_reports/daily_report_{date_str}.xlsx"
            df.to_excel(report_file, index=False)
            print(f"[+] Daily report saved to {report_file}")
            
    elif args.weekly:
        report.generate_weekly_report(args.date)
        
    elif args.monthly:
        report.generate_monthly_report(args.month, args.year)
        
    else:
        print("[!] Please specify a report type: --daily, --weekly, or --monthly")
        parser.print_help()

if __name__ == "__main__":
    main()
