# bot_chat_telegram

# create 'api-key-google.json'
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----..",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "...",
  "universe_domain": "googleapis.com"
}

# creat 'config.json'
{
    "TELEGRAM_TOKEN": "...", // key telegram
    "SERVICE_ACCOUNT_FILE": "api-key-google.json",
    "SPREADSHEET_ID": "..." //key sheet
}
