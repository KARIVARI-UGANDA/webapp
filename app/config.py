import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod-use-32-chars")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./karivari.db")
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")
    insurance_flat_fee_usd: float = float(os.getenv("INSURANCE_FLAT_FEE_USD", "15.0"))
    booking_hold_minutes: int = int(os.getenv("BOOKING_HOLD_MINUTES", "30"))
    cancellation_free_days: int = int(os.getenv("CANCELLATION_FREE_DAYS", "7"))
    cancellation_half_refund_days: int = int(os.getenv("CANCELLATION_HALF_REFUND_DAYS", "2"))
    payment_provider: str = os.getenv("PAYMENT_PROVIDER", "paystack")
    kyc_provider: str = os.getenv("KYC_PROVIDER", "manual")
    manual_kyc_enabled: bool = os.getenv("MANUAL_KYC_ENABLED", "true").lower() == "true"

    # Paystack
    paystack_secret_key: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    paystack_public_key: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")

    # Flutterwave (MTN Uganda MoMo / Airtel Money)
    flutterwave_secret_key: str = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
    flutterwave_public_key: str = os.getenv("FLUTTERWAVE_PUBLIC_KEY", "")
    flutterwave_base_url: str = os.getenv("FLUTTERWAVE_BASE_URL", "https://api.flutterwave.com/v3")

    # Redirect URLs for Flutterwave hosted checkout
    payment_redirect_url: str = os.getenv("PAYMENT_REDIRECT_URL", "http://localhost:8080/payments/callback")

    # Stripe (card / international payments)
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    stripe_currency: str = os.getenv("STRIPE_CURRENCY", "usd")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Email / SMTP
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "noreply@karivari.ug")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "Kari Vari Uganda")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # Resend (HTTP email API — required on Render, falls back to SMTP locally)
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")

    # App
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8080")


settings = Settings()
