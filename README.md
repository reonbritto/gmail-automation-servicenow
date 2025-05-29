# ServiceNow Gmail Ticket Automation with CrewAI

This project uses CrewAI to automate the processing of ServiceNow tickets received via Gmail. It identifies ServiceNow notifications, extracts key information, and drafts appropriate responses based on predefined user preferences and ServiceNow best practices.

## Key Features

-   **Automated ServiceNow Ticket Identification**: Detects emails related to ServiceNow tickets (Incidents, Service Requests, etc.).
-   **Information Extraction**: Parses ticket details such as ticket number, priority, user, and description from email content.
-   **Contextual Response Generation**: Creates draft replies tailored to ServiceNow ticket types, leveraging templates and guidelines from `knowledge/user_preference.txt`.
-   **SLA Adherence**: Considers SLA information (to be configured in `user_preference.txt`) for prioritizing and formulating responses.
-   **Customizable Knowledge Base**: Utilizes `knowledge/user_preference.txt` for ServiceNow instance details, response templates, escalation paths, and communication style guides.
-   **Drafts for Review**: Saves generated responses as drafts in Gmail for user review before sending.

## Project Structure

```
.
├── README.md                   # This documentation file
├── pyproject.toml              # Python project configuration
├── Dockerfile                   # Docker configuration file
├── src/                        # Source code for the project
│   └── gmail_crew_ai/
│       ├── api.py              # FastAPI application
│       ├── config/
│       │   ├── agents.yaml     # Agent configurations
│       │   └── tasks.yaml      # Task configurations
│       ├── main.py             # Main application entry point
│       └── ...                 # Other source files
├── knowledge/                  # Knowledge base for CrewAI
│   └── user_preference.txt    # User-specific preferences and templates
├── output/                     # Output files (e.g., fetched emails, drafts)
└── .env                        # Environment variables (not included in repo)
```

## Installation & Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/reonbritto/email-automation
    cd email-automation
    ```

2.  **Create and activate a virtual environment**:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:

    ```bash
    crewai install
    pip install fastapi uvicorn
    ```

4.  **Configure environment variables**:

    Create a `.env` file in the root directory with the following variables:

    ```
    # Choose your LLM provider
    # OpenAI (Recommended)
    MODEL=openai/gpt-4o-mini
    OPENAI_API_KEY=your_openai_api_key

    # Or Gemini
    # MODEL=gemini/gemini-2.0-flash
    # GEMINI_API_KEY=your_gemini_api_key

    # Gmail credentials
    EMAIL_ADDRESS=your_email@gmail.com
    APP_PASSWORD=your_app_password
    ```

    <details>
    <summary><b>🔑 How to create a Gmail App Password</b></summary>

    1.  Go to your Google Account settings at [myaccount.google.com](https://myaccount.google.com/)
    2.  Select **Security** from the left navigation panel
    3.  Under "Signing in to Google," find and select **2-Step Verification** (enable it if not already enabled)
    4.  Scroll to the bottom and find **App passwords**
    5.  Select **Mail** from the "Select app" dropdown
    6.  Select **Other (Custom name)** from the "Select device" dropdown
    7.  Enter `Gmail CrewAI` as the name
    8.  Click **Generate**
    9.  Copy the 16-character password that appears (spaces will be removed automatically)
    10.  Paste this password in your `.env` file as the `APP_PASSWORD` value
    11.  Click **Done**

    **Note**: App passwords can only be created if you have 2-Step Verification enabled on your Google account.
    </details>

5.  **Configure ServiceNow-specific settings**:

    Update `knowledge/user_preference.txt` with your ServiceNow instance details, SLA guidelines, response templates for ticket types (Incident, Request), and escalation procedures.

## Usage

### Option 1: Run with CrewAI CLI

```bash
# Activate your virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the application
crewai run
```

You'll be prompted to enter the number of emails to process (default is 5).

### Option 2: Run with FastAPI Server

```bash
# Start the FastAPI server (use 0.0.0.0 to make it accessible from other machines)
uvicorn src.gmail_crew_ai.api:app --reload --host 0.0.0.0 --port 8000

# Or to run in the background:
nohup uvicorn src.gmail_crew_ai.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

Once running, access the interactive API documentation at:
- http://localhost:8000/docs (or http://your-server-ip:8000/docs)

## API Endpoints

The FastAPI server provides the following endpoints:

- **GET `/emails/unread`**: Fetch unread emails from your inbox
  - Query param: `limit` (default: 5)
  - Example: `curl http://localhost:8000/emails/unread?limit=10`

- **GET `/emails/thread-history`**: Get conversation history for an email thread
  - Query params: `email_id`, `include_attachments`, `max_depth`
  - Example: `curl http://localhost:8000/emails/thread-history?email_id=12345`

- **POST `/emails/draft-reply`**: Draft a contextual reply to an email
  - Body: `email_id`, `body`, `subject`, `include_history`, `max_history_depth`

- **POST `/crew/run`**: Run the full email processing crew
  - Query param: `email_limit`
  - Example: `curl -X POST http://localhost:8000/crew/run?email_limit=5`

## End-to-End Testing

1. **Fetch Unread Emails:**  
   - Use `/emails/unread` endpoint or `crewai run`.
   - Confirm emails are fetched and saved to `output/fetched_emails.json`.

2. **Thread History:**  
   - Use `/emails/thread-history?email_id=...`.
   - Confirm full conversation is returned.

3. **Draft Reply:**  
   - Use `/emails/draft-reply` with a valid email ID and body.
   - Confirm draft appears in your Gmail Drafts.

4. **Full Crew Run:**  
   - Use `/crew/run?email_limit=5`.
   - Confirm output files are generated and drafts are created as expected.

5. **API Testing:**  
   - Use Swagger UI at `/docs` to test all endpoints interactively.

## Special Features

- **🧠 Smart Response Generation**: The AI intelligently determines which emails actually need responses
- **✍️ Custom Drafts**: Responses are tailored to the email context and include proper formatting
- **🧵 Advanced Threading**: Properly tracks and manages email threads with References and In-Reply-To headers
- **📚 Conversation History**: Maintains full context of conversations for more relevant replies
- **🔄 Accurate Threading**: Ensures replies appear correctly threaded in email clients
- **👥 Participant Awareness**: Identifies all participants in conversation threads for better context

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Running with Docker

1.  **Build the Docker image**:

    ```bash
    docker build -t gmail-crewai-app .
    ```

2.  **Run the container (with your .env file)**:

    ```bash
    docker run -d --env-file .env -p 8000:8000 gmail-crewai-app
    ```

    - The API will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)
    - If running on a remote server, replace `localhost` with your server's IP.

3.  **(Optional) Mount output directory**:

    ```bash
    docker run -d --env-file .env -p 8000:8000 -v $(pwd)/output:/app/output gmail-crewai-app
    ```

**Notes:**
- Ensure your `.env` file is in the project root and contains all required secrets.
- For Podman, use `podman` instead of `docker` in the above commands.
- You can also run in CLI mode by overriding the CMD in the Docker run command if needed.