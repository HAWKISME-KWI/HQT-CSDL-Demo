<div align="center">

# Badminton Court Management System

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/download/)
[![Git](https://img.shields.io/badge/Git-2.0+-F05032?logo=git&logoColor=white)](https://git-scm.com/downloads)
[![Release](https://img.shields.io/badge/Release-v1.0.0-success)](https://github.com/HAWKISME-KWI/HQT-CSDL-Demo/releases)
[![GitHub Stars](https://img.shields.io/github/stars/HAWKISME-KWI/HQT-CSDL-Demo?style=social)](https://github.com/HAWKISME-KWI/HQT-CSDL-Demo/stargazers)

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
|   ├──  test
|       ├── attack_double_booking.py
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
---
## Some Bug On Annomally Transaction
### Lost Updated
To exploit this bug:
```bash
cd test
py attack_double_booking.py
```
Then you will see your booking with the booking uid is rejected, which must be booked!
### Phantom Read
This one you can see if you check the court and some one have booked that court in the time you see, when you refresh or click into the "Loc" button, you will see the new row
### Non-Repeatable Read
This can be see while y check the court price, when another change the court price then you will the this!
## Technologies Used
* Python 3.12
* PostgreSQL
* SQL / PL/pgSQL
* python-dotenv
---
## Contributors
This project was developed as part of the **Database Management Systems (HQT-CSDL)** course.
