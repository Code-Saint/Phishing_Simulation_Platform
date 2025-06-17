# 🎣 Phishing Simulation Platform

A secure and lightweight **Phishing Simulation Web App** designed to help organizations train employees to recognize phishing attempts. This tool mimics phishing attacks in a safe environment and provides real-time feedback, analytics, and awareness training.

---

## 🚀 Features

- ✉️ Send simulated phishing emails  
- 🪝 Fake password reset page to catch unsafe behavior  
- 📊 Admin dashboard with detailed analytics  
- ✅ Feedback page showing users they fell for a phishing trap  
- 💅 Stylish UI with modern glassmorphism effects  
- 🛡️ Secure handling of credentials and email delivery via Mailtrap  

---

## 🛠️ Getting Started

Follow these steps to set up and run the project locally.

### 1. 📧 Set Up Mailtrap

- Create a free account at [Mailtrap.io](https://mailtrap.io).
- Create a new inbox and navigate to **Inbox → SMTP Settings**.
- Copy the SMTP credentials.

### 2. 📝 Configure `.env`

In your project root, create a `.env` file and add the following:

```env
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
```

Replace the placeholders with your Mailtrap credentials.

### 3. 📦 Install Dependencies

Install all required Python packages by running:

```bash
pip install -r docs/requirements.txt
```

### 4. 🗃️ Initialize the Database

Create the SQLite database:

```bash
python db/init_db.py
```

### 5. ▶️ Run the Application

Launch the Flask app:

```bash
python app.py
```

Your local Flask server will start, and the terminal will show a URL (e.g., http://127.0.0.1:5000).Then open the URL shown in your terminal (e.g., http://127.0.0.1:5000) in your browser.

---

## 💡 How to Use the Simulation

1. **Homepage**: Click the **Launch a Simulation** button.
2. **Send Email**: Enter the recipient’s name and email, then click **Send Email**.
3. **Mailtrap**: Go to your Mailtrap inbox and view the newly received phishing email.
4. **Reset Password**: Click the link in the email to open the fake password reset page.
5. **Submit**: Enter the same email and a new password.
6. **Awareness Page**: A message appears: “⚠️ You Just Fell for a Phishing Simulation!”
7. **Return to Dashboard**: Use the provided button to go back.
8. **Admin Panel**: Navigate to `http://<your-local-ip>:5000/admin` to view activity logs and analytics.

---


