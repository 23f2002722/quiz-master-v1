# QuizMaster - Challenge Your Mind

## About the Project
QuizMaster is a Flask-based web application designed to provide an interactive quiz platform. Users can register, log in, and attempt quizzes, while admins can manage users, quizzes, and questions. The project follows the Model-View-Controller (MVC) architecture to ensure a structured and maintainable codebase.

## Architecture
The application is organized using the MVC architecture:
- **Controllers:**
  - `controllers_login.py`: Manages user authentication (login, registration) and session handling.
  - `controllers_admin.py`: Provides functionality for admin users to create, manage, and delete quizzes, chapters, questions, and users.
  - `controllers_users.py`: Handles user interactions such as attempting quizzes, viewing scores, and retrieving summaries.
- **Templates:**
  - Located in the `templates/` directory, these files use Jinja2 to render dynamic HTML pages.
- **Models:**
  - Defined in `models.py`, using SQLAlchemy to manage database interactions.

## Features Implemented
### Core Features:
- **User Registration & Authentication**
  - Users can sign up and log in with authentication handled using session cookies.
  - User sessions are maintained securely using Flask's session management.

- **Admin Management**
  - Admins can create and manage quizzes, chapters, questions, and users.
  - Admins can delete and create all necessary entities within the system.

- **Quiz Functionality**
  - Users can attempt available quizzes.
  - Quizzes have a timer and track user progress.
  - Users can navigate between questions before submitting the quiz.
  - Submitted quizzes are scored automatically.

- **Score & Summary**
  - Users can view their quiz scores.
  - Admins and users can access a summary of quiz attempts.

- **Search Functionality**
  - Users and admins can search for quizzes, questions, and other relevant data.

## How to Run the Project
Follow these steps to set up and run the application:

### 1. Create a Virtual Environment
```sh
python -m venv venv
```

### 2. Activate the Virtual Environment
- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```sh
  source venv/bin/activate
  ```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Run the Application
```sh
flask run
```

The application should now be running, and you can access it at `http://127.0.0.1:5000/` in your browser.

---

