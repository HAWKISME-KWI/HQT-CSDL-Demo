<div align="center">

# Badminton Court Management System

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/download/)
[![Git](https://img.shields.io/badge/Git-2.0+-F05032?logo=git&logoColor=white)](https://git-scm.com/downloads)
[![Release](https://img.shields.io/badge/Release-v1.0.0-success)](https://github.com/HAWKISME-KWI/HQT-CSDL-Demo/releases)

Database Management System Course Project
A badminton court booking and management system developed using **Python 3.12** and **PostgreSQL**.
</div>

## Prerequisites

* Python 3.12
* PostgreSQL
* Git

---

## Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/HAWKISME-KWI/HQT-CSDL-Demo.git
cd HQT-CSDL-Demo
```

### 2. Create and Activate a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

The `.env` file can be obtained from the project maintainers.

### 5. Run the Application

```bash
cd src
python main.py
```

---

## Project Structure

```text
HQT-CSDL-Demo/
│
├── src/
│   ├── main.py
│   └──  services/
|       ├── db_services.sql
│
├── sql/
│   ├── schema.sql
│   ├── views.sql
│   ├── function.sql
|   ├── rls.sql
|   ├── bucket_rls.sql
│   └── trigger.sql
│
├── config/
|   ├──db.py
├── requirements.txt
├── .env
└── README.md
```

---
## Features
* User Management
* Court Management
* Court Booking
* Payment Management
* Database Views
* Database Functions
* Triggers
* Reporting and Statistics
---
## Technologies Used
* Python 3.12
* PostgreSQL
* SQL / PL/pgSQL
* python-dotenv
---
## Contributors
This project was developed as part of the **Database Management Systems (HQT-CSDL)** course.
