# data-analyst-agent

🧠 Auto Data Analysis Pipeline with LLM & Retry Mechanism

This project automates data analysis code generation using a Large Language Model (LLM), with built-in metadata extraction, code execution, and an iterative error-fixing loop.
🚀 Features

    Automated Metadata Extraction – LLM decides if metadata from attachments is needed before solving.

    End-to-End Code Generation – From problem statement to executable Python code.

    Safe Code Execution – Runs inside a controlled Python environment with an allowed libraries whitelist.

    Iterative Error Fixing – If the generated code fails, errors are sent back to the LLM to fix and retry.

    JSON Output – Final results are returned in a clean JSON format.

    Optional Attachments – Supports CSV, Excel, HTML, and other data sources.

🛠 How It Works

<img width="1315" height="635" alt="image" src="https://github.com/user-attachments/assets/7475774e-3326-4cc3-9073-6454008c3aa0" />



    Input

        questions.txt: Contains the data analysis task.

        Optional attachments: datasets, reports, or web pages.

    Metadata Extraction

        LLM generates Python code to extract metadata from attachments.

        Metadata is executed in a Python sandbox.

    Solution Code Generation

        LLM generates Python code to solve the data analysis task using the task + metadata.

    Execution & Retry Loop

        Code is executed.

        If errors occur:

            Errors + last code are sent to the LLM for fixing.

            Execution is retried up to a maximum number of attempts.

    Final Output

        Returns JSON with the result.

        If no errors, process stops early.




📦 Installation


# Install dependencies
```
pip install -r requirements.txt
```

⚙️ Environment Variables

Create a .env file in the root folder:
```
GEMINI_API_KEY=your_gemini_api_key_here

SAVE_LOGS=true
```


▶️ Running the FastAPI Server

Run the server with:
```
uvicorn main:app --reload
```
📡 Making a Request

You can send your data analysis request with questions.txt and optional attachments using curl:
```
curl "https://app.example.com/api/" \
  -F "questions.txt=@question.txt" \
  -F "image.png=@image.png" \
  -F "data.csv=@data.csv"
```
Notes:

    questions.txt → Required, contains the data analysis task.

    Attachments → Optional (.csv, .txt, .png, etc.).

📝 Example

questions.txt:
```
Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings containing the answer.

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
   Return as a base-64 encoded data URI, `"data:image/png;base64,iVBORw0KG..."` under 100,000 bytes.
```
Sample Response:
```
[
  1,
  "Titanic",
  0.485782,
  "data:image/png;base64,iVBORw0KG... (response truncated)"
]

```
