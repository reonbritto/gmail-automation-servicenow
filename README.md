# Gmail Response Generator with CrewAI 📧✨

Gmail Response Generator with CrewAI is a streamlined email management system that focuses on two key tasks:

1. **Fetching your unread emails** from Gmail
2. **Generating appropriate responses** for emails that need attention

## ✨ Features

- **📥 Email Fetching**: Automatically retrieves unread emails from your Gmail inbox
- **📊 Smart Analysis**: Analyzes email content to determine which messages need responses
- **💬 Automated Responses**: Generates draft responses for important emails that need replies
- **🧵 Smart Threading**: Enhanced conversation continuity with accurate threading of emails even in long conversations
- **📝 Context-Aware Replies**: Drafts replies with full conversation history for better context
- **📚 Thread History**: Automatically retrieves complete thread history for comprehensive context before replying
- **🌐 REST API**: Access all functionality through a RESTful API interface
- **🪢 Empty Subject Handling**: Properly threads replies even for emails missing subject lines

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/reonbritto/email-automation
cd email-automation

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
crewai install
pip install fastapi uvicorn
```

## ⚙️ Configuration

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

1. Go to your Google Account settings at [myaccount.google.com](https://myaccount.google.com/)
2. Select **Security** from the left navigation panel
3. Under "Signing in to Google," find and select **2-Step Verification** (enable it if not already enabled)
4. Scroll to the bottom and find **App passwords**
5. Select **Mail** from the "Select app" dropdown
6. Select **Other (Custom name)** from the "Select device" dropdown
7. Enter `Gmail CrewAI` as the name
8. Click **Generate**
9. Copy the 16-character password that appears (spaces will be removed automatically)
10. Paste this password in your `.env` file as the `APP_PASSWORD` value
11. Click **Done**

**Note**: App passwords can only be created if you have 2-Step Verification enabled on your Google account.
</details>

## 📧 How It Works

This application uses the IMAP (Internet Message Access Protocol) to securely connect to your Gmail account. Here's how it works:

<details>
<summary><b>🔄 IMAP Connection Process</b></summary>

1. **Secure Connection**: The application establishes a secure SSL connection to Gmail's IMAP server (`imap.gmail.com`).

2. **Authentication**: It authenticates using your email address and app password (not your regular Google password).

3. **Mailbox Access**: Once authenticated, it can access your inbox to:
   - Read unread emails
   - Save draft responses

4. **Safe Disconnection**: After each operation, the connection is properly closed to maintain security.

IMAP allows the application to work with your emails while they remain on Google's servers, unlike POP3 which would download them to your device. This means you can still access all emails through the regular Gmail interface.

**Security Note**: Your credentials are only stored locally in your `.env` file and are never shared with any external services.
</details>

<details>
<summary><b>🧵 Smart Threading System</b></summary>

1. **Thread Detection**: The system identifies related messages by analyzing Message-ID, References, and In-Reply-To headers.

2. **History Retrieval**: For any email that's part of a thread, the complete conversation history is retrieved.

3. **Chronological Sorting**: All messages in a thread are sorted chronologically for proper context.

4. **Latest Message Tracking**: The system always uses the latest message in a thread for proper reply threading.

5. **Participant Analysis**: All participants in the conversation are identified for context awareness.

This threading system ensures that responses maintain conversation context and appear properly threaded in email clients, creating a seamless experience for both you and your recipients.
</details>

---

## 📊 Dataset Details

**Source & Types:**  
This project does not use a traditional ML dataset. Instead, it operates directly on your Gmail inbox using the IMAP protocol. The "dataset" consists of your real, live email data (subjects, senders, bodies, threads, etc.) fetched securely from Gmail.

**Data Preprocessing:**  
- Email headers and bodies are decoded and cleaned (HTML tags removed, whitespace normalized).
- Threading information is extracted using Message-ID, References, and In-Reply-To headers.
- Emails are categorized (e.g., important, newsletter, etc.) using rule-based logic and, optionally, LLM-powered classification.
- For model-based features, emails are tokenized and formatted for LLM input.

**Parameters Considered for Model/Agent:**  
- Email subject, sender, date, body, thread context, and message metadata.
- Thread history (previous messages in the conversation).
- User preferences (from a knowledge file, e.g., signature, tone, priorities).

**Target Parameters for Inference:**  
- Whether a response is needed (binary classification).
- Drafted reply content (text generation).
- Suggested labels or actions (categorization).

---

## 🏋️ Model Training, Testing & Validation

**Model Training:**  
- This project leverages pre-trained Large Language Models (LLMs) such as OpenAI GPT-4 or Gemini, accessed via API.
- No custom supervised training is performed on your emails; instead, prompt engineering and context assembly are used for inference.

**Testing & Validation:**  
- The system is tested end-to-end using real email samples.
- Validation is performed by checking if the AI correctly identifies emails needing a response and generates appropriate drafts.
- Manual review of generated drafts is recommended for quality assurance.

**Model Saving & Format:**  
- Since LLMs are accessed via API, there is no local model file to save.
- If you fine-tune or train your own model, save it in a standard format (e.g., HuggingFace `.bin` or `.pt` for PyTorch, `.h5` for TensorFlow).

---

## 🖥️ Hardware & Software Requirements

**Hardware:**  
- For inference: Any modern CPU (cloud VM or local machine). No GPU required for API-based LLMs.
- For training (if you fine-tune): GPU recommended (NVIDIA with CUDA support).

**Software:**  
- Python 3.8+
- Required packages: `crewai`, `fastapi`, `uvicorn`, `pydantic`, `requests`, `beautifulsoup4`, etc.
- Access to OpenAI, Gemini, or Azure OpenAI API for LLM inference.

---

## 📈 Metrics & Model Evaluation

**Metrics Used:**  
- **Response Accuracy:** Percentage of emails correctly identified as needing a response.
- **Draft Quality:** Manual review for tone, relevance, and completeness.
- **Threading Accuracy:** Replies appear correctly threaded in Gmail.
- **Latency:** Time to generate a draft (should be <10s per email).

**Why This Model:**  
- LLMs provide state-of-the-art performance for text understanding and generation.
- Rule-based filters ensure only relevant emails are processed, reducing noise.

---

## 🚀 Model Inference Details

- Inference is performed by sending email context (subject, body, thread history) to the LLM via API.
- The LLM returns a draft reply, which is then saved as a Gmail draft.
- No email data is stored outside your environment; all processing is local except for LLM API calls.

---

## 🏗️ High-Level Architecture Diagram

```
+-------------------+       +-------------------+       +-------------------+
|   Gmail Inbox     |<----->|   CrewAI System   |<----->|    LLM API        |
| (via IMAP/SMTP)   |       | (Python, FastAPI) |       | (OpenAI/Gemini)   |
+-------------------+       +-------------------+       +-------------------+
         |                          |                             |
         |<-----User Preferences----|                             |
         |                          |                             |
         |<-----API Requests/CLI----|                             |
         |                          |                             |
         |<-----Drafts Saved--------|                             |
```

---

## 🔍 Usage

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

## 🧰 API Endpoints

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

---

## 🧪 End-to-End Testing

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

---

## 🌟 Special Features

- **🧠 Smart Response Generation**: The AI intelligently determines which emails actually need responses
- **✍️ Custom Drafts**: Responses are tailored to the email context and include proper formatting
- **🧵 Advanced Threading**: Properly tracks and manages email threads with References and In-Reply-To headers
- **📚 Conversation History**: Maintains full context of conversations for more relevant replies
- **🔄 Accurate Threading**: Ensures replies appear correctly threaded in email clients
- **👥 Participant Awareness**: Identifies all participants in conversation threads for better context

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐳 Running with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t gmail-crewai-app .
   ```

2. **Run the container (with your .env file):**
   ```bash
   docker run -d --env-file .env -p 8000:8000 gmail-crewai-app
   ```

   - The API will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)
   - If running on a remote server, replace `localhost` with your server's IP.

3. **(Optional) Mount output directory:**
   ```bash
   docker run -d --env-file .env -p 8000:8000 -v $(pwd)/output:/app/output gmail-crewai-app
   ```

**Notes:**
- Ensure your `.env` file is in the project root and contains all required secrets.
- For Podman, use `podman` instead of `docker` in the above commands.
- You can also run in CLI mode by overriding the CMD in the Docker run command if needed.