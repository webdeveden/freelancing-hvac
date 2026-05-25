"""
settings.py — Application configuration via Pydantic Settings

All environment variables are validated and typed here.
Import `settings` anywhere in the app to access config values.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    environment: str = "development"
    port: int = 8000

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hvac_db"
    db_user: str = "hvac_user"
    db_password: str = "hvacpassword"

    # Anthropic
    anthropic_api_key: str = ""
    ai_model: str = "claude-haiku-4-5-20251001"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Backend bridge
    backend_url: str = "http://localhost:3001"
    internal_api_secret: str = ""

    # Public-facing base URL used in TwiML action callbacks.
    # Must be set to your ngrok/tunnel URL so Twilio can reach the gather endpoint.
    # Example: https://abc123.ngrok.io
    public_url: str = ""

    # Business info for system prompt
    business_name: str = "HVAC Pro Services"
    business_phone: str = "+15550010000"
    service_area: str = "Dallas, TX and surrounding areas"
    business_hours: str = "Monday to Friday 8 AM to 6 PM, Saturday 9 AM to 2 PM"
    emergency_hours: str = "24/7 emergency service available"

    # Call routing — receptionist forwarding
    receptionist_phone:   str = ""                          # E.164, e.g. +12145550123. Empty = AI always answers.
    business_hours_start: str = "08:00"                     # HH:MM 24h
    business_hours_end:   str = "18:00"                     # HH:MM 24h (exclusive)
    business_days:        str = "Mon,Tue,Wed,Thu,Fri,Sat"   # comma-separated strftime %a values
    business_timezone:    str = "America/Chicago"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
