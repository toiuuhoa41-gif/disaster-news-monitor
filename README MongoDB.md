# Disaster Monitor

## Overview

Disaster Monitor is a real-time disaster news monitoring system designed to crawl, analyze, and provide updates on disaster-related articles. The system aggregates data from various news sources, processes it for relevance, and presents it through a user-friendly dashboard and real-time updates.

## Features

- **Real-time Monitoring**: Continuously crawls disaster news articles from multiple sources.
- **Data Analysis**: Utilizes NLP techniques to classify articles and extract relevant information.
- **Dashboard**: Provides statistics and insights on disaster articles, including severity breakdowns and trends.
- **WebSocket Support**: Offers real-time updates through WebSocket connections for immediate notifications of new articles.

## Project Structure

```
disaster-news-monitor
├── mongodb
│   └── api
│       ├── main.py                # Entry point for the FastAPI application
│       ├── daily_scheduler.py      # Scheduler for daily tasks
│       ├── config                  # Configuration settings
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   └── database.py
│       ├── routers                 # API routers for different functionalities
│       │   ├── __init__.py
│       │   ├── system.py
│       │   ├── articles.py
│       │   ├── dashboard.py
│       │   ├── sources.py
│       │   ├── keywords.py
│       │   ├── regions.py
│       │   ├── realtime.py
│       │   └── internal.py
│       ├── services                # Business logic for various functionalities
│       │   ├── __init__.py
│       │   ├── crawl_service.py
│       │   ├── stats_service.py
│       │   ├── maintenance_service.py
│       │   ├── sources_service.py
│       │   ├── keywords_service.py
│       │   ├── articles_service.py
│       │   ├── classification_service.py
│       │   └── websocket_service.py
│       ├── models                  # Data models for the application
│       │   ├── __init__.py
│       │   ├── article.py
│       │   ├── source.py
│       │   ├── keyword.py
│       │   ├── region.py
│       │   └── stats.py
│       ├── schemas                 # Pydantic schemas for data validation
│       │   ├── __init__.py
│       │   ├── system.py
│       │   ├── article.py
│       │   ├── dashboard.py
│       │   ├── source.py
│       │   ├── keyword.py
│       │   ├── region.py
│       │   └── classification.py
│       ├── utils                   # Utility functions and logging
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   └── helpers.py
│       └── websockets              # WebSocket handling for real-time updates
│           ├── __init__.py
│           └── disaster_feed.py
├── requirements.txt                # Project dependencies
├── .env.example                    # Example environment variables
└── README.md                       # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/disaster-news-monitor.git
   cd disaster-news-monitor
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by copying `.env.example` to `.env` and configuring the necessary values.

## Usage

To start the application, run the following command:
```
uvicorn mongodb.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

The API provides various endpoints for interacting with the disaster monitoring system. You can access the documentation at `http://localhost:8000/docs` after starting the server.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.