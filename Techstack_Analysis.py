from Report import report

if __name__ == '__main__':
    
    stack_report = report.Report()
    stack_report.plot_database_stats()
    stack_report.plot_websites_per_branch()