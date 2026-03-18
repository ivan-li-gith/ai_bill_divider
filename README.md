# AI Bill Divider (Split Em 💸)

**Split Em** is an AI full-stack web application designed to automate the parsing of utility bills and calculate fair monthly expense splits among roommates. It leverages LLMs to eliminate manual data entry and provides a centralized dashboard for tracking household finances


## 🚀 Live Demo
Access the application here: [Split Em](https://split-em.com)


## ✨ Key Features
* **AI Data Extraction**: Automatically parses complex PDF utility statements to extract service periods and balances using the OpenAI GPT-4o API
* **Dynamic Roommate Management**: Add or remove roommates directly within the upload workflow to adjust splits
* **Automated Rollover Tracking**: Automatically carries over unpaid balances to the next month's total for each individual
* **Visual Analytics**: Interactive dashboards that provides insights into monthly spending trends and service breakdowns
* **Secure Authentication**: Integrated with Supabase Auth for secure email/password and Google OAuth 2.0 sign-in


## 🛠️ Technical Stack
* **Frontend**: Flask, HTML, CSS
* **Backend**: Gunicorn
* **AI Engine**: OpenAI GPT-4o
* **Authentication**: Supabase Auth (OAuth 2.0)
* **Database**: MySQL hosted on AWS RDS using SQLAlchemy and Pandas
* **Infrastructure & Security**:
    * **AWS EC2**: Containerized deployment via Docker and Docker Compose
    * **AWS CloudFront & Route 53**: Handles secure connections and domain name routing



## 📦 Local Development

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ivan-li-gith/ai_bill_divider.git
    cd ai_bill_divider
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python -m venv .venv

    # Git Bash Windows:
    source .venv/Scripts/activate

    # PowerShell Windows:
    .venv\Scripts\activate
    
    # Mac/Linux:
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file in the root directory with the following keys. You can gather these keys from the following sources:
    * `OPENAI_API_KEY`: [OpenAI API](https://openai.com/index/openai-api/)
    * `SUPABASE_URL` & `SUPABASE_KEY`: [Supabase](https://supabase.com/)
    * `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`: [AWS RDS Console](https://aws.amazon.com/)
    * `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: [Google Cloud Console](https://cloud.google.com/)
    * `APP_SECRET_KEY`: Generate a random string (`python -c 'import os; print(os.urandom(24).hex())'`)

5.  **Run the application**:
    ```bash
    python run.py
    ```


## 📖 How to Use
1.  **Login**: Sign up for a new account via email/password or through Google
2.  **Manage Roommates**: Navigate to the **Roommates** tab to add the people you are splitting with
3.  **Upload Bills**: Drag and drop your utility PDF statements into the **Upload Bills** tab
4.  **Review**: Verify the AI-extracted data in the staging area and click "Confirm & Save to Database". If unable to read files, manually enter details
5.  **Track Payments**: Use the **History** tab to mark bills as "Paid" and see how it automatically affects the next month's rollover totals
