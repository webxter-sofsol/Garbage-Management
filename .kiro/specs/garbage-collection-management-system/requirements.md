# Requirements Document

## Introduction

The Garbage Collection Management System is a web-based platform that connects citizens with municipal waste management authorities. The system enables citizens to report waste management issues, request pickups, and track complaint resolution while providing authorities with tools for staff assignment, route optimization, real-time monitoring, and analytics. The platform aims to improve transparency, reduce response times, and enhance citizen engagement in urban cleanliness initiatives.

## Glossary

- **System**: The Garbage Collection Management System web application
- **Citizen**: A registered user who reports waste management issues and requests services
- **Authority**: A municipal administrator who manages complaints, assigns staff, and monitors operations
- **Staff_Member**: A waste collection worker assigned to handle complaints and perform pickups
- **Complaint**: A citizen-reported waste management issue with location, description, and optional photos
- **OTP**: One-Time Password sent via email for authentication
- **Pickup_Request**: A citizen request for scheduled waste collection at a specific location
- **Collection_Route**: A planned path for waste collection with scheduled stops
- **Bin_Location**: A designated waste collection point marked on the system map
- **Notification**: An automated message sent to users about complaint status changes
- **Analytics_Dashboard**: A visual interface displaying waste management metrics and statistics
- **Response_Time**: The duration between complaint submission and staff assignment
- **Resolution_Status**: The current state of a complaint (pending, assigned, in-progress, resolved, closed)

## Requirements

### Requirement 1: User Registration and Authentication

**User Story:** As a citizen, I want to register and log in securely using my email, so that I can access the system and report waste management issues.

#### Acceptance Criteria

1. WHEN a new user provides a valid email address, THE System SHALL create a user account and send an OTP to the email
2. WHEN a user enters a valid OTP within 10 minutes of generation, THE System SHALL authenticate the user and grant access
3. IF an OTP expires after 10 minutes, THEN THE System SHALL reject the authentication attempt and prompt for a new OTP request
4. THE System SHALL store user credentials securely using password hashing with salt
5. WHEN a user requests login, THE System SHALL generate a new OTP and invalidate any previous unused OTPs for that email

### Requirement 2: Complaint Reporting

**User Story:** As a citizen, I want to report garbage problems with location and photos, so that authorities can address the issue quickly.

#### Acceptance Criteria

1. WHEN a citizen submits a complaint, THE System SHALL capture the complaint description, location coordinates, timestamp, and optional photo attachments
2. THE System SHALL validate that complaint descriptions contain at least 10 characters and at most 500 characters
3. THE System SHALL accept photo uploads in JPEG, PNG, or WebP format with maximum file size of 5MB per photo
4. THE System SHALL allow up to 3 photos per complaint
5. WHEN a complaint is submitted, THE System SHALL assign a unique complaint ID and store it in the MySQL database
6. THE System SHALL set the initial Resolution_Status to "pending" for all new complaints
7. WHEN a complaint is successfully saved, THE System SHALL display a confirmation message with the complaint ID to the citizen

### Requirement 3: Pickup Request Scheduling

**User Story:** As a citizen, I want to request scheduled waste pickups at my location, so that I can dispose of waste conveniently.

#### Acceptance Criteria

1. WHEN a citizen creates a pickup request, THE System SHALL capture the pickup location, preferred date, waste type, and estimated quantity
2. THE System SHALL validate that the preferred pickup date is at least 24 hours in the future
3. THE System SHALL store the pickup request in the MySQL database with status "pending"
4. WHEN a pickup request is submitted, THE System SHALL generate a unique request ID and notify the citizen

### Requirement 4: Complaint Management by Authorities

**User Story:** As an authority, I want to view all reported complaints with filtering options, so that I can prioritize and manage waste management issues effectively.

#### Acceptance Criteria

1. THE System SHALL display all complaints to authorities with complaint ID, location, description, photos, timestamp, and Resolution_Status
2. THE System SHALL provide filtering options by Resolution_Status, date range, and location
3. THE System SHALL provide sorting options by timestamp, location, and Resolution_Status
4. WHEN an authority selects a complaint, THE System SHALL display full complaint details including citizen contact information

### Requirement 5: Staff Assignment

**User Story:** As an authority, I want to assign collection staff to complaints, so that issues can be resolved efficiently.

#### Acceptance Criteria

1. WHEN an authority assigns a Staff_Member to a complaint, THE System SHALL update the Resolution_Status to "assigned" and record the assignment timestamp
2. THE System SHALL store the Staff_Member ID, name, and contact information associated with the complaint
3. WHEN a staff assignment is made, THE System SHALL send a notification to the assigned Staff_Member with complaint details
4. WHEN a staff assignment is made, THE System SHALL send a notification to the citizen who filed the complaint
5. THE System SHALL prevent assignment of a Staff_Member who is already assigned to more than 10 active complaints

### Requirement 6: Real-time Location Tracking

**User Story:** As an authority, I want to track collection staff locations in real-time, so that I can monitor field operations and optimize routes.

#### Acceptance Criteria

1. WHEN a Staff_Member is on duty, THE System SHALL receive and store location updates at intervals of 30 seconds or less
2. THE System SHALL display Staff_Member locations on a map interface with their current status
3. THE System SHALL calculate and display the estimated time of arrival at assigned complaint locations based on current position
4. WHILE a Staff_Member is traveling to a complaint location, THE System SHALL update the Resolution_Status to "in-progress"

### Requirement 7: Complaint Resolution and Documentation

**User Story:** As a staff member, I want to mark complaints as resolved with before and after photos, so that I can document completed work.

#### Acceptance Criteria

1. WHEN a Staff_Member marks a complaint as resolved, THE System SHALL require upload of at least one "after" photo
2. THE System SHALL store the resolution timestamp and photos in the MySQL database
3. WHEN a complaint is marked resolved, THE System SHALL update the Resolution_Status to "resolved" and send a notification to the citizen
4. THE System SHALL calculate and store the Response_Time as the duration between complaint submission and resolution

### Requirement 8: Citizen Notification System

**User Story:** As a citizen, I want to receive instant notifications about my complaint status, so that I stay informed about resolution progress.

#### Acceptance Criteria

1. WHEN a Staff_Member is assigned to a complaint, THE System SHALL send a notification to the citizen with Staff_Member name and estimated arrival time
2. WHEN the Resolution_Status changes to "in-progress", THE System SHALL send a notification to the citizen
3. WHEN a complaint is marked "resolved", THE System SHALL send a notification to the citizen with resolution details and photos
4. THE System SHALL deliver notifications via email within 60 seconds of the status change event
5. WHERE the citizen has enabled browser notifications, THE System SHALL also send browser push notifications

### Requirement 9: Garbage Bin Location Mapping

**User Story:** As a citizen, I want to view garbage bin locations on a map, so that I can find the nearest disposal point.

#### Acceptance Criteria

1. THE System SHALL display all Bin_Locations on an interactive map with markers
2. WHEN a citizen views the map, THE System SHALL show the citizen's current location and calculate distances to nearby bins
3. THE System SHALL provide filtering options by bin type (general waste, recyclable, organic)
4. WHEN a citizen selects a bin marker, THE System SHALL display bin details including address, type, and collection schedule

### Requirement 10: Collection Route Scheduling

**User Story:** As an authority, I want to create and publish collection route schedules, so that citizens know when waste will be collected in their area.

#### Acceptance Criteria

1. WHEN an authority creates a Collection_Route, THE System SHALL capture the route name, scheduled stops, collection days, and time windows
2. THE System SHALL validate that time windows do not overlap for the same Staff_Member
3. THE System SHALL store Collection_Routes in the MySQL database and make them visible to citizens
4. WHEN a citizen views collection schedules, THE System SHALL display routes relevant to their registered location

### Requirement 11: Analytics Dashboard

**User Story:** As an authority, I want to view analytics on complaints, response times, and neighborhood performance, so that I can make data-driven decisions.

#### Acceptance Criteria

1. THE System SHALL calculate and display total complaints by Resolution_Status for selectable time periods
2. THE System SHALL calculate and display average Response_Time by neighborhood and overall
3. THE System SHALL display complaint volume trends using line charts for the past 30 days
4. THE System SHALL rank neighborhoods by Response_Time, complaint volume, and resolution rate
5. THE System SHALL provide export functionality for analytics data in CSV format
6. THE System SHALL refresh analytics data automatically every 5 minutes while the dashboard is open

### Requirement 12: Automated Reporting

**User Story:** As an authority, I want to generate automated reports on waste management operations, so that I can track performance and compliance.

#### Acceptance Criteria

1. THE System SHALL generate daily summary reports containing total complaints received, resolved, and pending
2. THE System SHALL generate weekly performance reports containing average Response_Time, Staff_Member productivity, and neighborhood statistics
3. THE System SHALL generate monthly trend reports containing complaint volume trends, resolution rate trends, and citizen satisfaction scores
4. WHEN a report is generated, THE System SHALL store it in the database and send it via email to designated authorities
5. THE System SHALL allow authorities to download historical reports in PDF format

### Requirement 13: Citizen Rating and Feedback

**User Story:** As a citizen, I want to rate the service quality after complaint resolution, so that I can provide feedback on staff performance.

#### Acceptance Criteria

1. WHEN a complaint is marked "resolved", THE System SHALL prompt the citizen to provide a rating from 1 to 5 stars
2. THE System SHALL allow citizens to provide optional text feedback with maximum 300 characters
3. THE System SHALL store ratings and feedback in the MySQL database linked to the complaint and Staff_Member
4. THE System SHALL calculate and display average ratings for each Staff_Member on the Analytics_Dashboard
5. WHEN a citizen submits a rating, THE System SHALL update the complaint Resolution_Status to "closed"

### Requirement 14: Archive and Historical Data Management

**User Story:** As an authority, I want to archive old complaints and maintain historical records, so that I can analyze long-term trends and maintain system performance.

#### Acceptance Criteria

1. WHEN a complaint has Resolution_Status "closed" for more than 90 days, THE System SHALL move it to the archive database table
2. THE System SHALL maintain archived complaints accessible for viewing but exclude them from active complaint lists
3. THE System SHALL allow authorities to search archived complaints by date range, location, and complaint ID
4. THE System SHALL retain archived data for at least 5 years before permanent deletion

### Requirement 15: Mobile-Responsive Interface

**User Story:** As a citizen, I want to access the system from my mobile device, so that I can report issues and track complaints on the go.

#### Acceptance Criteria

1. THE System SHALL render all user interfaces responsively for screen widths from 320px to 1920px
2. THE System SHALL optimize touch interactions for mobile devices with touch targets at least 44x44 pixels
3. WHEN accessed from a mobile device, THE System SHALL use the device's GPS for automatic location capture in complaints
4. THE System SHALL compress images uploaded from mobile devices to reduce bandwidth usage while maintaining readability

### Requirement 16: Data Validation and Error Handling

**User Story:** As a user, I want to receive clear error messages when I provide invalid input, so that I can correct mistakes and complete my tasks.

#### Acceptance Criteria

1. WHEN a user submits invalid data, THE System SHALL display a descriptive error message indicating the specific validation failure
2. THE System SHALL validate email addresses using RFC 5322 standard format
3. THE System SHALL validate location coordinates to ensure they fall within valid latitude (-90 to 90) and longitude (-180 to 180) ranges
4. IF a database operation fails, THEN THE System SHALL log the error details and display a user-friendly error message without exposing technical details
5. THE System SHALL validate file uploads to prevent execution of malicious code by checking file headers and extensions

### Requirement 17: Session Management and Security

**User Story:** As a user, I want my session to remain secure and automatically expire after inactivity, so that my account is protected from unauthorized access.

#### Acceptance Criteria

1. WHEN a user successfully authenticates, THE System SHALL create a session with a unique session token
2. THE System SHALL expire sessions after 30 minutes of inactivity
3. WHEN a session expires, THE System SHALL redirect the user to the login page and display a session timeout message
4. THE System SHALL use HTTPS for all data transmission between client and server
5. THE System SHALL implement CSRF protection for all state-changing operations

### Requirement 18: Database Backup and Recovery

**User Story:** As a system administrator, I want automated database backups, so that data can be recovered in case of system failure.

#### Acceptance Criteria

1. THE System SHALL perform automated MySQL database backups daily at 2:00 AM local time
2. THE System SHALL retain daily backups for 30 days before automatic deletion
3. THE System SHALL store backup files in a separate storage location from the primary database
4. THE System SHALL verify backup integrity by performing test restoration monthly
5. WHEN a backup operation fails, THE System SHALL send an alert email to system administrators

