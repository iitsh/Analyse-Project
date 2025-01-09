```markdown
# Analyse Project

## Description

The Analyse Project is a web application built with Django to perform advanced data analysis. It allows users to register, upload data files, generate interactive charts, and produce PDF reports.

## Features

- **User Registration and Authentication**
- **Data File Upload and Management**
- **Data Visualization with Charts**
- **Automated Statistical Analysis**
- **PDF Report Generation and Download**

## Prerequisites

- Python 3.x
- Django 4.x (or a compatible version)
- Virtualization tool (Pipenv or virtualenv)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/iitsh/analyse_project.git
   ```

2. **Navigate to the project directory:**
   ```bash
   cd analyse_project
   ```

3. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

4. **Activate the virtual environment:**

   - **On macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

   - **On Windows:**
     ```bash
     .\venv\Scripts\activate
     ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Apply database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser to access Django admin:**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

9. **Access the application:**
   Open your browser and go to [http://127.0.0.1:8000](http://127.0.0.1:8000) to use the app.

## Usage

1. **Register:** Create an account on the application.
2. **Upload Data:** Upload your CSV files for analysis.
3. **Analyze and Visualize:** Use the app's tools to explore and analyze your data.
4. **Export Reports:** Generate and download analysis reports in PDF format.


## Author

- Rayane Berrada - (https://github.com/iitsh)