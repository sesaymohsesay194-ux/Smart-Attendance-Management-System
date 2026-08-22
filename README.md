MK# 📊 Smart Attendance Management System

## 🚀 Overview

The Smart Attendance Management System is a web-based application built using Flask and SQLite. It automates the traditional attendance process by providing an efficient, accurate, and secure platform for managing student attendance.

---

## 🎯 Features

* 👨‍🎓 Student, Teacher, and Admin Login System
* 📅 Attendance marking by teachers
* 📊 Real-time attendance tracking & dashboards
* 📉 Low attendance detection (< 75%)
* 📄 PDF report generation
* 🔐 OTP-based password reset (Email)
* 🤖 AI Chatbot for attendance queries
* 👤 Face Recognition Login (OpenCV + face_recognition)
* 🚫 Duplicate attendance prevention

---

## 🛠️ Tech Stack

* **Backend:** Flask (Python)
* **Database:** SQLite
* **Frontend:** HTML, CSS
* **Libraries:**

  * OpenCV
  * face_recognition
  * Flask-Mail
  * ReportLab
  * Google Gemini API

---

## 📁 Project Structure

```
Smart-Attendance-Management-System/
│
├── app.py                 # Main Flask application
├── database.db            # SQLite database
├── seed_students.py       # Database seeding
├── create_teacher_table.py
│
├── templates/             # HTML templates
├── static/                # CSS, images
├── faces/                 # Stored face images
│
└── .env                   # Environment variables
```

---

## ⚙️ Installation & Setup

1. Clone the repository:

```
git clone https://github.com/your-username/Smart-Attendance-Management-System.git
cd Smart-Attendance-Management-System
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Setup environment variables (.env):

```
MAIL_PASSWORD=your_email_password
GEMINI_API_KEY=your_api_key
```

4. Run the application:

```
python app.py
```

5. Open in browser:

```
http://127.0.0.1:5000/
```

---

## 🔐 Default Credentials

* **Admin Login**

  * Username: `admin`
  * Password: `admin@123`

---

## 📊 How It Works

1. Teacher logs in and selects class & subject
2. Attendance is marked and stored in database
3. System prevents duplicate entries
4. Students can view attendance and reports
5. Face recognition allows quick login
6. AI chatbot provides attendance insights

---

## ⚠️ Limitations

* Passwords stored in plain text
* SQLite not suitable for large-scale deployment
* Basic security implementation

---

## 🚀 Future Improvements

* 🔒 Password hashing (bcrypt)
* ☁️ Cloud deployment (AWS / Render)
* 📱 Mobile application
* 🔔 Notification system
* 📊 Advanced analytics dashboard

---

## 💡 Unique Features

* Face Recognition Login
* AI Chatbot Integration
* OTP-based Password Reset
* Automated PDF Reports

---

## 👨‍💻Author

**Medish**

---

## ⭐ Conclusion

This project demonstrates a complete attendance management system with modern features like AI, automation, and biometric authentication, making it more efficient than traditional methods.
