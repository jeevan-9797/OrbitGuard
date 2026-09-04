"""
Application Configuration
Module: app.config
"""

import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Satellite Multi-Agent AI System"
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/satellite_ai?sslmode=prefer")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    simulation_tick_rate_ms: int = int(os.getenv("SIMULATION_TICK_RATE_MS", 1000))
    simulation_active_scenario: str = os.getenv("SIMULATION_ACTIVE_SCENARIO", "SCENARIO_A")


settings = Settings()
