import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod-use-32-chars")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))
    database_url: str = os.environ["DATABASE_URL"]
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")
    insurance_flat_fee_usd: float = float(os.getenv("INSURANCE_FLAT_FEE_USD", "15.0"))
    booking_hold_minutes: int = int(os.getenv("BOOKING_HOLD_MINUTES", "30"))
    cancellation_free_days: int = int(os.getenv("CANCELLATION_FREE_DAYS", "7"))
    cancellation_half_refund_days: int = int(os.getenv("CANCELLATION_HALF_REFUND_DAYS", "2"))
    payment_provider: str = os.getenv("PAYMENT_PROVIDER", "stripe")
    kyc_provider: str = os.getenv("KYC_PROVIDER", "manual")
    manual_kyc_enabled: bool = os.getenv("MANUAL_KYC_ENABLED", "true").lower() == "true"


settings = Settings()
