# ServiceNow Developer Email Assistant with CrewAI

This project uses CrewAI to assist ServiceNow developers by managing and responding to development-related emails. It leverages an advanced Large Language Model (e.g., Gemini) to understand email context, draft replies to technical queries, summarize code review feedback, or acknowledge deployment notifications. The `knowledge/user_preference.txt` file serves as a general reference for developer preferences and technical notes.

## Key Features

-   **Automated Email Triage**: Identifies emails relevant to ServiceNow development tasks.
-   **Contextual Response Generation**: Utilizes an advanced LLM (e.g., Gemini) to draft responses to common developer queries, code discussions, or system notifications, drawing on its broad knowledge and the provided email context.
-   **Developer Preferences Reference**: The `knowledge/user_preference.txt` file can store ServiceNow instance details, coding standards, and common script patterns for user reference or high-level context.
-   **Drafts for Review**: Saves generated responses as drafts in Gmail for developer review before sending.
-   **Customizable**: Easily adapt the agent's persona and high-level guidance.

## Project Structure

```
.
├── README.md
├── docker-compose.yml
├── dockerfile
├── output
│   ├── drafts
│   └── fetched_emails.json
├── pyproject.toml
├── requirements.txt
├── src
│   ├── gmail_crew_ai
│   │   ├── api.py
│   │   ├── config
│   │   │   ├── agents.yaml
│   │   │   ├── knowledge.yaml
│   │   │   └── tasks.yaml
│   │   ├── main.py
│   │   └── utils.py
│   └── main.py
└── .env
```

## Installation and Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/servicenow-developer-email-assistant.git
    cd servicenow-developer-email-assistant
    ```

2.  **Create a virtual environment and activate it**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables**:

    Copy `.env.example` to `.env` and update the values with your Gmail API credentials and ServiceNow instance details.

5.  **Configure the knowledge base**:

    Edit `knowledge/user_preference.txt` to include your ServiceNow instance details, common script patterns, API usage notes, and coding standards.

## Usage

### Running the Assistant

To start the ServiceNow Developer Email Assistant, run:

```bash
crewai run
```

This will start the assistant, which will check for new emails, triage them, and draft responses as needed.

### Accessing the API

The assistant also provides a RESTful API to access its functionality. To run the API server:

```bash
uvicorn src.gmail_crew_ai.api:app --reload
```

The API will be available at `http://localhost:8000`. You can use the interactive API documentation at `http://localhost:8000/docs` to explore the available endpoints.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: This project is a fictional example for illustrative purposes.