# Blog Assist - AI Blog Writer Agent

**Blog Assist** is an intelligent AI agent designed to automate the creation and publishing of high-quality blog posts. It integrates powerful Large Language Models (LLMs) like Google Gemini and OpenAI with your WordPress site to streamline your content strategy.

## 🚀 Key Features

*   **Dual AI Power**: Choose between **Google Gemini** (Cost-effective/Free) or **OpenAI** (GPT-4o) for content generation.
*   **WordPress Integration**: Seamlessly publishes posts to your WordPress site.
    *   **Draft Mode**: Review content before it goes live.
    *   **Publish Mode**: Instant publishing for fully automated workflows.
*   **Automated Scheduling**: Set the agent to run every 3, 6, 12, 24, or 48 hours to maintain a consistent posting schedule.
*   **Customizable Topics**: Generate content for specific niches (Tech, Travel, Health, etc.) or custom topics.
*   **Simulated Mode**: Test your workflow and connectivity without using real API credits.

## 🛠️ Installation & Setup

1.  **Prerequisites**:
    *   Python 3.8+ installed.
    *   A WordPress site with **Application Passwords** enabled (wp-admin > Users > Profile).

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    ```bash
    python -m streamlit run app.py
    ```

4.  **Access the Dashboard**:
    Open your browser and navigate to `http://localhost:8501` (or the port shown in your terminal).

## ⚙️ Configuration Guide

1.  **AI Provider**:
    *   Select **Google Gemini** and enter your API Key.
    *   Or select **OpenAI** and provide your key.
2.  **WordPress Credentials**:
    *   **URL**: Your full site URL (e.g., `https://mysite.com`).
    *   **Username**: Your WordPress username.
    *   **Application Password**: The generated password from your profile (do not use your login password).
3.  **Content Settings**:
    *   Choose a **Topic** or enter a custom one.
    *   Set the **Word Count**.
    *   Select **Post Status** (Draft or Publish).
4.  **Save Configuration**: Click the "Save Configuration" button to store your settings locally.

## 🤖 Usage

*   **Manual Run**: Click **"Run Once Now"** to generate a single post immediately.
*   **Start Agent**: Select a schedule interval and click **"Start Agent"**. The app will run in the background and log its activity.

## 📝 License

This project is open-source and available for personal and commercial use.
