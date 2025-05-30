# Gmail & ServiceNow Email Automation

This project automates the process of reading emails from Gmail, analyzing them, and generating appropriate responses using AI. It can handle both regular email correspondence and ServiceNow technical tickets.

## Features

- Fetch unread emails from Gmail
- Analyze email content to determine if a response is needed
- Generate professional and contextually appropriate responses
- Support for technical ServiceNow tickets
- Save response drafts for review before sending
- Mark emails as read

## Setup

### Prerequisites

- Python 3.10 or newer
- Gmail account with application password enabled

### Environment Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd email-automation
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -e .
   ```

4. Create a `.env` file in the root directory with your Gmail credentials:
   ```
   GMAIL_USER=your.email@gmail.com
   GMAIL_PASSWORD=your-app-password
   OPENAI_API_KEY=your-openai-api-key
   ```
   
   Note: For Gmail, you need to generate an "App Password" in your Google account settings.

### Directory Structure

```
email-automation/
│
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py             # Entry point for the application
│   ├── email_service.py    # Module for email-related functions
│   ├── ai_service.py       # Module for AI response generation
│   └── config.py          # Configuration settings
│
├── tests/                  # Unit and integration tests
│   ├── __init__.py
│   ├── test_email_service.py
│   └── test_ai_service.py
│
├── .env                     # Environment variables
├── requirements.txt         # Python package dependencies
└── README.md                # Project documentation
```

## Usage

1. Activate the virtual environment:
   ```
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the application:
   ```
   python src/main.py
   ```

3. Access the API documentation at `http://localhost:8000/docs`.

## API Endpoints

- `POST /emails/fetch`: Fetch unread emails from Gmail
- `POST /emails/analyze`: Analyze email content and determine response
- `POST /emails/respond`: Generate and save response draft
- `POST /emails/mark-read`: Mark email as read in Gmail

## Testing

1. Install test dependencies:
   ```
   pip install -r requirements-test.txt
   ```

2. Run the tests:
   ```
   pytest
   ```

## Troubleshooting

- If you encounter issues with Gmail authentication, ensure that "Less secure app access" is enabled in your Google account settings.
- For any AI-related errors, check your OpenAI API key and usage limits.

## Contributing

Contributions are welcome! Please submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.