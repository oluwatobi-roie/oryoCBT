The File structure is seen below

#The Name here#


flask_mcq_app/
│
├── app.py                    # Main Flask application
├── mcq_app.db                # SQLite database file (created at runtime)
│
├── static/                   # Static files (CSS, JS, images)
│   ├── css/
│   │   └── styles.css        # Custom styles
│   └── js/
│       └── dashboard.js      # JavaScript for dynamic UI (progress bar, navigation)
│
├── templates/                # HTML templates
│   ├── base.html             # Base template for layout inheritance
│   ├── login.html            # Login page
│   ├── dashboard.html        # User dashboard (question navigation)
│   ├── admin_dashboard.html  # Admin dashboard
│   └── analytics.html        # Analytics page
│
├── migrations/               # Migrations (if using Flask-Migrate)
│
└── README.md                 # Documentation for setting up and running the app