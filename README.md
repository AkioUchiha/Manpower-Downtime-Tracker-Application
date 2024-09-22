# Manpower-Downtime-Tracker-Application
A Python-based Flask application to monitor employee downtime during lunch breaks using a scanning system. This Flask-based application tracks employee lunch breaks in real-time. It displays the following features:

Live Tracking: The application records and displays employee IDs when they first scan out for lunch, along with a live timer showing the elapsed time since their scan.

Returned Employees: When an employee scans their ID again after lunch, their ID is removed from the live tracking list, indicating they've returned.

Delayed Arrivals: If an employee scans back in after 45 minutes, their ID is flagged and moved to a separate "Delayed Arrivals" list.

Real-Time Monitoring: The application continuously updates to reflect the current status of employees out for lunch and those returned.

Database Management: A "Clear Database" button allows users to reset all stored data easily.
