# 🤖 Agentic Sales Multi-Agent System

An AI-powered multi-agent sales automation platform that automates the lead generation and outreach workflow for **office-chair businesses**.

The system discovers potential businesses, filters qualified leads, researches them using web search, finds contact information, generates personalized sales emails, asks for human approval before sending, sends approved emails through Gmail, and exports the final results to Excel.

---

## 🚀 Overview

Traditional sales prospecting requires sales teams to manually:

- Find potential businesses
- Collect business information
- Identify relevant prospects
- Research companies
- Find business contact information
- Write personalized outreach emails
- Send emails
- Maintain lead records

This project automates these repetitive tasks using a **stateful multi-agent architecture built with LangGraph**.

The system uses specialized agents and external tools to create an end-to-end sales automation workflow while keeping a **human-in-the-loop approval step before sending emails**.

---

## 🎯 Problem Statement

Sales teams spend significant time on repetitive lead-generation and outreach activities.

For example, selling office chairs to businesses requires identifying businesses that may need office furniture, researching those businesses, finding contact information, creating personalized emails, sending them, and maintaining records.

This project aims to automate that workflow using **Agentic AI**, while still keeping the human in control of outbound communication.

---

# ✨ Key Features

### 🔎 AI Lead Discovery

Discovers potential businesses using Google Maps/Places data through Apify.

Example:

```text
Find dental clinics in Hyderabad
```

The system processes the request and searches for relevant businesses.

---

### 🎯 Intelligent Lead Filtering

The Filtering Agent evaluates discovered businesses and determines which leads are relevant to the sales objective.

Only qualified leads continue to the research and outreach stages.

---

### 📧 Business Email Discovery

The system attempts to find publicly available business email addresses.

It uses multiple approaches:

```text
Business Website
       ↓
Website Email Extraction
       ↓
If unavailable
       ↓
Web Search
       ↓
Business Email
```

This provides a fallback mechanism when a business listing does not contain an email address.

---

### 🔬 AI-Powered Lead Research

The Research Agent uses Tavily to gather information about qualified businesses.

Research can include:

- Company information
- Recent business activity
- Website information
- Business context
- Sales-relevant information

The collected information is then passed to the Email Agent for personalization.

---

### ✍️ Personalized AI Email Generation

The Email Agent generates personalized sales emails based on the lead's available information and research.

The product being promoted by the system is:

> **Office chairs**

Generated emails contain:

- Personalized subject
- Relevant business context
- Personalized message
- Clear call-to-action

The generated email is also validated before being presented for approval.

---

# 👨‍💼 Human-in-the-Loop Approval

The system does not automatically send every generated email.

Before sending an email, the workflow pauses and requests human approval.

The user can choose:

```text
approve
edit
reject
```

### Approve

The email is sent through Gmail.

### Edit

The user can modify the:

- Subject
- Email body

The updated email is then shown for approval again.

### Reject

The email is rejected and the workflow continues with the next lead.

This provides human oversight over AI-generated outbound communication.

---

# 🔄 Sequential Lead Processing

Qualified leads are processed **one at a time**.

The workflow follows:

```text
Lead 1
   ↓
Research
   ↓
Email Generation
   ↓
Human Approval
   ↓
Send
   ↓
Lead 2
   ↓
Research
   ↓
Email Generation
   ↓
Human Approval
   ↓
Send
   ↓
Lead 3
   ↓
...
   ↓
Excel Export
```

The system completes the workflow for the current lead before moving to the next qualified lead.

There is **no artificial delay, timer, sleep, or rate limiter** between leads.

---

# 📊 Excel Reporting

After processing the qualified leads, the system exports the results to an Excel file.

The report can contain information such as:

- Business name
- Email
- Phone
- Website
- Category
- City
- Qualification
- Qualification reason
- Qualification confidence
- Research depth
- Business research
- Hiring signals
- Expansion signals
- Workplace signals
- Email subject
- Email body
- Email status

This creates a structured record of the sales campaign results.

---

# 🧠 Multi-Agent Architecture

The system consists of specialized agents.

```text
                         USER REQUEST
                              │
                              ▼
                     ┌─────────────────┐
                     │  Manager Agent  │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Maps Agent    │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Filtering Agent │
                     └────────┬────────┘
                              │
                       Qualified Leads
                              │
                              ▼
                     ┌─────────────────┐
                     │ Research Agent  │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Email Agent   │
                     └────────┬────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Human Approval     │
                    │ Approve / Edit /   │
                    │ Reject             │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Send Email Agent   │
                    └─────────┬──────────┘
                              │
                              ▼
                       Next Qualified Lead
                              │
                              ▼
                    ┌────────────────────┐
                    │  Excel Export      │
                    └────────────────────┘
```

---

# 🤖 Agents

## 1. Manager Agent

Responsible for understanding the user's request and extracting structured information such as:

- Business type
- Location
- Search query
- Lead limit

The Manager Agent also helps separate the **target business** from the **product being sold**.

---

## 2. Maps Agent

Responsible for discovering potential businesses.

### Tool

- Apify Google Places / Google Maps scraper

The agent also integrates email discovery when contact information is missing from the business listing.

---

## 3. Filtering Agent

Responsible for evaluating discovered businesses and identifying qualified prospects.

Only qualified leads continue through the sales pipeline.

---

## 4. Research Agent

Responsible for researching qualified leads using Tavily.

The research information is used to create more relevant and personalized sales emails.

### Tool

- Tavily

---

## 5. Email Agent

Responsible for generating personalized sales emails using the LLM.

The agent uses:

- Lead information
- Business information
- Research results

to generate an outreach email specifically for the office-chair sales workflow.

---

## 6. Send Email Agent

Responsible for:

- Human approval
- Email editing
- Email rejection
- Sending approved emails

The agent uses LangGraph's interrupt mechanism to pause the workflow and wait for human input.

---

## 7. Excel Export Agent

Responsible for converting the final lead and email results into a structured Excel report.

---

# 🏗️ LangGraph Workflow

The project uses LangGraph `StateGraph` to maintain shared state across multiple agents.

The simplified workflow is:

```text
START
  │
  ▼
Manager
  │
  ▼
Maps
  │
  ▼
Filtering
  │
  ▼
Initialize Lead Processing
  │
  ▼
Research
  │
  ▼
Email Generation
  │
  ▼
Human Approval
  │
  ├─────────────── Edit ──────────────┐
  │                                   │
  │                                   ▼
  │                            Approval Again
  │
  ├─────────────── Reject
  │
  └─────────────── Approve
                          │
                          ▼
                     Send Email
                          │
                          ▼
                  Save Lead Result
                          │
                   More Leads?
                     /       \
                   Yes        No
                    │          │
                    ▼          ▼
                 Research   Excel Export
                               │
                               ▼
                              END
```

---

# 🧠 Stateful Workflow

The workflow maintains shared state between agents.

Important state fields include:

```text
user_request
user_email
business_type
search_query
location
lead_limit
leads
qualified_leads
researched_leads
current_lead_index
processed_leads
processed_emails
emails
approval_status
excel_file
workflow_plan
current_stage
retry_counts
status
error
```

This allows different agents to communicate through a shared workflow state rather than operating as isolated scripts.

---

# 🧰 Tech Stack

## Programming

- Python 3.11

## AI / LLM

- NVIDIA Nemotron
- LangChain
- LangGraph
- Pydantic

## External AI / Data Tools

- Tavily
- Apify

## APIs

- Gmail API
- Google OAuth 2.0
- Apify API

## Backend

- FastAPI

## Data / Reporting

- OpenPyXL
- Excel

## Workflow State / Persistence

- LangGraph Checkpointer
- SQLite

## Development

- VS Code
- Git
- GitHub
- Python Virtual Environment

---

# 📁 Project Structure

```text
sales_multi_agent/
│
├── agents/
│   ├── manager_agent.py
│   ├── maps_agent.py
│   ├── filtering_agent.py
│   ├── research_agent.py
│   ├── email_agent.py
│   ├── send_email_agent.py
│   └── excel_export_agent.py
│
├── core/
│   ├── llm.py
│   ├── state.py
│   ├── checkpointer.py
│   └── ...
│
├── tools/
│   ├── email_finder.py
│   ├── email_tools.py
│   ├── tavily_tools.py
│   ├── excel_tools.py
│   ├── token_manager.py
│   └── ...
│
├── workflow/
│   ├── graph.py
│   └── routing.py
│
├── data/
│   └── exports/
│
├── config/
│   └── ...
│
├── main.py
├── requirements.txt
├── .env
└── .gitignore
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

```bash
cd sales_multi_agent
```

---

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

Example:

```env
NVIDIA_API_KEY=your_nvidia_api_key
TAVILY_API_KEY=your_tavily_api_key
APIFY_API_TOKEN=your_apify_api_token
```

Additional credentials may be required depending on the enabled integrations.

### ⚠️ Security

Never commit API keys, OAuth credentials, or other secrets to GitHub.

Make sure `.gitignore` contains:

```gitignore
.env
.venv/
__pycache__/
*.pyc
data/exports/
```

---

# 📧 Gmail API Setup

The Gmail integration uses OAuth authentication.

General setup:

1. Create a Google Cloud project.
2. Enable the Gmail API.
3. Configure the OAuth consent screen.
4. Create OAuth client credentials.
5. Download the required credentials file.
6. Run the authentication flow.
7. Authorize the Gmail account.

The application uses OAuth instead of storing the Gmail account password.

---

# ▶️ Running the Project

Start the workflow with:

```bash
python main.py
```

The application asks:

```text
What leads do you want to find?
>
```

Example:

```text
Find dental clinics in Hyderabad
```

Then:

```text
How many leads? (1-50)
>
```

Example:

```text
5
```

Finally, provide the authenticated Gmail address.

---

# 💻 Example Workflow

### User Request

```text
Find dental clinics in Hyderabad
```

### Processing

```text
1. Manager understands the request
            ↓
2. Maps Agent discovers businesses
            ↓
3. Filtering Agent qualifies leads
            ↓
4. Research Agent researches Lead 1
            ↓
5. Email Agent generates personalized email
            ↓
6. Human reviews email
            ↓
7. Approved email is sent
            ↓
8. Lead 2 starts
            ↓
9. Process continues
            ↓
10. Final results exported to Excel
```

---

# 👨‍💼 Example Human Approval

The system pauses before sending:

```text
============================================================
EMAIL APPROVAL REQUIRED
============================================================

Business: Example Dental Clinic
Email: contact@example.com

Subject:
Office Chairs for Your Growing Team

Body:
...

Choose: approve / edit / reject
>
```

### Approve

```text
approve
```

The email is sent through Gmail.

### Edit

```text
edit
```

The system asks for the updated subject and body and then requests approval again.

### Reject

```text
reject
```

The email is not sent and the workflow proceeds to the next lead.

---

# 🔄 Sequential Processing Example

For three qualified leads:

```text
Lead 1
  │
  ├── Research
  ├── Generate Email
  ├── Approval
  └── Send
        │
        ▼
Lead 2
  │
  ├── Research
  ├── Generate Email
  ├── Approval
  └── Send
        │
        ▼
Lead 3
  │
  ├── Research
  ├── Generate Email
  ├── Approval
  └── Send
        │
        ▼
Excel Export
```

The workflow does not start the next lead until the current lead's processing is completed.

---

# 🧩 Challenges Solved

## 1. Stateful Multi-Agent Orchestration

Multiple agents need to read and update shared information throughout the workflow.

LangGraph state management is used to maintain information between agents.

---

## 2. Human-in-the-Loop Email Sending

AI-generated sales emails should not automatically be sent without user control.

LangGraph interrupts allow the workflow to pause before sending and wait for a human decision.

The user can:

```text
Approve
Edit
Reject
```

---

## 3. Sequential Lead Processing

Instead of processing all leads simultaneously, the system processes one qualified lead at a time.

This required tracking:

```text
current_lead_index
processed_leads
processed_emails
```

so that results from previous leads are preserved while the next lead is processed.

---

## 4. Missing Business Emails

Business listings do not always provide an email address.

The system uses:

```text
Website Email Extraction
          ↓
      If missing
          ↓
      Web Search
```

to improve contact discovery.

---

## 5. External API Failures

The project depends on external APIs such as Apify, Tavily, NVIDIA, and Gmail.

API failures are handled within the workflow, and Apify token management includes fallback handling for token-related failures.

---

## 6. Personalized Outreach

Instead of generating a generic sales email, the workflow first researches the business.

```text
Business
   ↓
Web Research
   ↓
Relevant Information
   ↓
LLM
   ↓
Personalized Email
```

This allows the generated outreach to use business-specific context.

---

# 📈 Project Capabilities

| Capability | Status |
|---|---|
| AI request understanding | ✅ |
| Google Maps lead discovery | ✅ |
| Lead filtering | ✅ |
| Business email discovery | ✅ |
| Website email extraction | ✅ |
| Web search fallback | ✅ |
| Tavily research | ✅ |
| AI email generation | ✅ |
| Human approval | ✅ |
| Email editing | ✅ |
| Email rejection | ✅ |
| Gmail sending | ✅ |
| Sequential lead processing | ✅ |
| Excel export | ✅ |
| LangGraph state management | ✅ |
| API failure handling | ✅ |
| FastAPI integration | ✅ |

---

# 📊 Workflow Stages

The complete sales workflow contains the following major stages:

```text
1. Request Understanding
2. Lead Discovery
3. Lead Qualification
4. Contact Discovery
5. Business Research
6. Personalized Email Generation
7. Human Approval
8. Email Sending
9. Result Storage
10. Excel Reporting
```

---

# 🔮 Future Improvements

Potential future improvements include:

- React / Next.js dashboard
- PostgreSQL-based lead management
- Redis-based task management
- Advanced lead scoring
- Email verification
- Improved lead deduplication
- Email delivery analytics
- Open and click tracking
- Automated follow-up sequences
- CRM integration
- Advanced agent routing
- LangSmith observability and evaluation
- Docker deployment
- Cloud deployment
- Automated sales campaign management

---

# 🎓 What I Learned

This project provided hands-on experience with:

- Agentic AI architecture
- Multi-agent systems
- LangGraph
- LangChain
- Stateful workflows
- LLM-powered automation
- Human-in-the-loop systems
- Tool integration
- API integration
- Web research
- Lead generation
- Sales automation
- Gmail OAuth
- Structured LLM outputs
- Error handling
- API fallback mechanisms
- Excel automation
- Git and GitHub

---

# 🔑 Key Engineering Concepts Demonstrated

### Agent Orchestration

Different specialized agents collaborate through a shared workflow state.

### Tool Calling

Agents interact with external services such as:

```text
Apify
Tavily
Gmail
```

### Human-in-the-Loop

Critical outbound actions require human approval.

### Stateful Execution

LangGraph maintains workflow state throughout the multi-step process.

### Error Handling

External API failures and missing information are handled without unnecessarily breaking the entire workflow.

### Sequential Processing

Each qualified lead is completely processed before the next lead starts.

---

# 🛡️ Security Considerations

The project is designed to keep sensitive credentials outside the source code.

Sensitive information should be stored in environment variables or OAuth credential files.

Never commit:

```text
.env
OAuth credentials
API keys
Access tokens
Private credentials
```

to the repository.

---

# 📌 Project Highlights

- Built a real-world **Agentic AI sales automation system**
- Implemented a **multi-agent architecture using LangGraph**
- Integrated multiple external APIs and AI tools
- Added **human approval before outbound email**
- Implemented **approve / edit / reject** workflow
- Built sequential lead processing
- Added automated business email discovery
- Added web-based lead research
- Generated personalized AI sales emails
- Automated Excel reporting
- Added API failure handling and token fallback mechanisms

---

# 👨‍💻 Author

## Mohammed Anas

BE Artificial Intelligence & Machine Learning

GitHub:

https://github.com/MohammedAnas5628

---

# ⭐ Project Goal

The goal of this project is to demonstrate how **Agentic AI can be used to automate a real-world business workflow** by combining:

```text
LLMs
 +
Specialized Agents
 +
External Tools
 +
APIs
 +
Human-in-the-Loop
 +
Stateful Workflow Orchestration
```

into an end-to-end sales automation platform.
