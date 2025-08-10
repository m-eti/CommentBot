# Telegram Commenting Bot Control Panel

A web-based control panel for managing a Telegram bot that automatically posts comments in channels. Built with Flask for the web interface and Telethon for interacting with the Telegram API.

## Features

- **Web-Based UI**: Easy-to-use interface to manage all bot functions.
- **Secure Access**: The control panel is protected by a password configured in a `config.json` file.
- **Multi-Account Management**: Add and remove multiple Telegram accounts to use for commenting.
- **Dynamic Comment List**: Add and remove comments that the bot will choose from randomly.
- **Start/Stop Control**: Easily start and stop the commenting process.
- **Live Logging**: View the bot's recent activity directly in the web UI.

## Prerequisites

- Python 3.10+
- A Telegram account
- Telegram `API_ID` and `API_HASH`. You can get these from my.telegram.org.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/m-eti/CommentBot
    cd CommentBot
    ```

2.  **Create a `requirements.txt` file:**
    This project depends on Flask and Telethon. Create a file named `requirements.txt` with the following content:
    ```
    flask
    telethon
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  **Start the application:**
    ```bash
    gunicorn --bind 0.0.0.0:8000 wsgi:application --reload
    ```
    The first time you run the application, it will create a `config.json` file in the root directory with default values.

2.  **Configure the application:**
    Open the newly created `config.json` file and edit it:
    -   Set your `API_ID` and `API_HASH` obtained from Telegram.
    -   Change the default `PASSWORD` from `"admin"` to something secure.

    Example `config.json`:
    ```json
    {
        "PASSWORD": "your_secure_password",
        "API_ID": "1234567",
        "API_HASH": "your_api_hash",
        "accounts": {},
        "comments": []
    }
    ```

3.  **Access the Control Panel:**
    Open your web browser and navigate to `http://127.0.0.1:5000`. You will be prompted to log in with the password you set in `config.json`.

## Usage

-   **Add Account**:
    1.  Enter a phone number and click "Get Verification Code".
    2.  Telegram will send a code to that account.
    3.  Enter the phone number, the received code, and the account's 2FA password (if it has one) and click "Add Account".

-   **Add Comment**: Enter the text for a new comment and click "Add Comment". The bot will randomly pick from this list.

-   **Control**: Use the "Start" and "Stop" buttons to control the bot's commenting activity.

-   **Manage Accounts/Comments**: You can delete accounts and comments from their respective lists using the "Delete" buttons.

## Running Tests

To run the included tests, you'll need `pytest`.

1.  **Install testing dependencies:**
    ```bash
    pip install pytest
    ```
2.  **Run the test suite:**
    ```bash
    pytest
    ```