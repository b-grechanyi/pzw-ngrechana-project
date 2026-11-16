pzw-ngrechana-project/
├── docker-compose.yml       # starts PostgreSQL
├── .env                     # your local settings; ignored by Git
├── .env.example             # example settings for someone cloning the project
├── .gitignore
└── api/
    ├── .venv/               # this project's Python environment; ignored by Git
    ├── requirements.txt     # backend Python packages
    ├── alembic/             # database migration setup
    ├── tests/               # backend tests
    └── app/
        ├── main.py          # starts and configures the API
        ├── core/            # configuration and database connection
        ├── models/          # database table definitions
        ├── schemas/         # API input and output shapes
        ├── repositories/    # database queries
        ├── services/        # library rules
        └── routers/         # API endpoints