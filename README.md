# 🚦 QueueLess – Smart College Queue Management System

> **A real-time digital queue management system designed to reduce waiting time and improve service management in colleges.**

---

## 📌 About The Project

**QueueLess** is a smart web-based queue management system developed for college environments.

In colleges, students often waste valuable time standing in queues at places such as:

- 🍔 College Canteen
- 🏢 Admin Office
- 💻 Computer Lab
- 📚 Library
- 💰 Accounts Office
- 📝 Examination Cell

QueueLess solves this problem by allowing students to **join queues digitally, monitor their position, and receive notifications before their turn**.

At the same time, administrators can manage queues, serve students, monitor activity, and view feedback through an admin dashboard.

---

## 🎯 Problem Statement

Traditional college queues can cause:

- Long waiting times
- Crowded service areas
- Unorganized queues
- Difficulty knowing when your turn will come
- Poor visibility for administrators
- Unnecessary time spent waiting

### 💡 Our Solution

QueueLess provides a centralized digital system where students can:

> **Join → Track → Get Notified → Get Served**

without physically standing in line.

---

# ✨ Key Features

## 👨‍🎓 Student Features

### 🔐 Student Registration & Login
- College ID-based registration
- Secure password-based login
- Student profile information
- College details

### 🏃 Digital Queue Joining
Students can join available college services digitally.

### 📊 Live Queue Tracking
Students can view:

- Queue number
- Current position
- People ahead
- Estimated waiting time
- Current serving status

### 🔔 Turn Notification
Students receive a notification before their turn so they don't have to continuously wait near the service counter.

### 📋 My Queue
Students can view their active queues and manage them.

### 📅 Activity Calendar
A dynamic calendar displays the student's queue activity and history.

### 💬 Feedback System
Students can:

- Submit feedback
- Give ratings
- View recent feedback
- Delete their own feedback

---

# 👨‍💼 Admin Features

## 🔐 Admin Authentication

Dedicated admin registration and login system.

## 🏢 Service Management

Administrators can manage college services such as:

| Service | Average Service Time |
|---|---:|
| College Canteen | 2 min |
| Admin Office | 5 min |
| Computer Lab | 3 min |
| Library | 4 min |
| Accounts Office | 5 min |
| Examination Cell | 5 min |

## 🎫 Queue Management

Administrators can:

- View waiting students
- Serve the next student
- Complete queues
- Monitor current servicing
- Track queue status

## 📈 Daily Activity

The dashboard provides service activity information so administrators can monitor completed services.

## 💬 Feedback Management

Administrators can view and manage feedback submitted by students.

---

# 🛠️ Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask
- Flask-CORS

### Database
- SQLite

### Development Tools
- Visual Studio Code
- Git
- GitHub

---

# 🏗️ System Architecture

```text
                 ┌─────────────────────┐
                 │      Student        │
                 │   Web Application   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Flask API       │
                 │      Backend        │
                 └──────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
      ┌───────────────┐          ┌────────────────┐
      │    SQLite     │          │     Admin      │
      │    Database   │          │    Dashboard   │
      └───────────────┘          └────────────────┘