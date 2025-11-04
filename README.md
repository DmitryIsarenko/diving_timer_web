# Diving Timer Web

A web application for systematic breath-holding training using controlled breathing methodology. Designed for freediving and other respiratory practices.

## 🚀 Features

- **4-Phase Breathing Cycle**: Inhale → Hold → Exhale → Hold (optional)
- **Voice Guidance**: Audio prompts in Russian for precise timing of each phase
- **Flexible Configuration**: Customizable duration for each training phase
- **Multiple Rounds**: Support for multiple cycles in a single training session
- **Progress Tracking**: Countdown timers for each phase and total session time
- **Pause and Resume**: Ability to pause and continue training sessions
- **Statistics**: Track workout results and progress over time

## ⚠️ Safety Warning

**IMPORTANT**: Breath-holding exercises should always be performed under the direct supervision of a qualified safety person. Training alone poses significant risks, including shallow water blackout, hypoxic blackout, and other potentially life-threatening conditions. Never practice breath-holding exercises without proper supervision and safety protocols in place.

## 🛠 Technologies

- **Backend**: Django 5.0.6
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Containerization**: Docker & Docker Compose
- **Voice Synthesis**: Web Speech API

## 📋 Requirements

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (for local development)

## 🚀 Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DmitryIsarenko/diving_timer_web.git
   cd diving_timer_web
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file with your values:
   ```env
   DB_NAME=diving_timer
   DB_USER=diving_timer_user
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=5432
   POSTGRES_VERSION=18
   ```

3. **Launch the application:**
   ```bash
   docker-compose up --build
   ```

4. **Open in browser:**
   ```
   http://localhost:8000
   ```

## 🏃‍♂️ Local Development

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the database:**
   - Install PostgreSQL locally
   - Create a database and user
   - Update environment variables in `.env`

4. **Run migrations:**
   ```bash
   cd diving_timer
   python manage.py migrate
   ```

5. **Start development server:**
   ```bash
   python manage.py runserver
   ```

## 📖 Usage

### Training Configuration

1. **Inhale Time**: Duration of the inhalation phase (seconds)
2. **Hold After Inhale**: Breath-hold duration after inhalation
3. **Exhale Time**: Duration of the exhalation phase
4. **Hold After Exhale**: Breath-hold duration after exhalation (optional)
5. **Number of Rounds**: How many cycles to perform

### Training Controls

- **Start**: Begin training with current settings
- **Pause**: Pause the current training session
- **Resume**: Continue a paused training session
- **Reset**: Return to settings and start over

### Voice Guidance

The application uses speech synthesis to announce the current training phase. Russian language voices are supported.

## 🐳 Docker Commands

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f django_diving_timer

# Execute commands in container
docker-compose exec django_diving_timer python manage.py shell
```

## 📁 Project Structure

```
diving_timer_web/
├── diving_timer/           # Main Django application
│   ├── diving_timer/       # Project settings
│   ├── timer/             # Timer application
│   │   ├── static/        # CSS and JavaScript
│   │   ├── templates/     # HTML templates
│   │   └── ...
│   └── manage.py
├── docker-compose.yaml     # Docker configuration
├── dockerfile             # Docker image
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables example
└── README.md
```

## 🔧 Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DB_NAME` | Database name | diving_timer |
| `DB_USER` | Database user | diving_timer_user |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `POSTGRES_VERSION` | PostgreSQL version | 18 |

## 🎯 Future Goals

The following features are planned for upcoming releases:

- **User Authentication**: Implement user registration and login system
- **Personal Statistics**: Maintain individual training history and progress tracking
- **Multilingual Support**: Add English version of the website interface and voice guidance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

## 📞 Contact

Dmitry Isarenko - isarenko.dmitry.it@gmail.com

Project Link: [https://github.com/DmitryIsarenko/diving_timer_web](https://github.com/DmitryIsarenko/diving_timer_web)

---

**Disclaimer**: Before beginning any intensive breath-holding training program, consult with a qualified medical professional. This application is a training tool and does not replace proper instruction, supervision, or medical advice.
