from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Format URL: postgresql+psycopg://<user>:<password>@<host>:<port>/<nama_db>
DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/todo"
# Database terpisah untuk testing, supaya data asli tidak ikut terhapus/berubah
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5432/todo_test"
)


# Konfigurasi aplikasi. Setiap field otomatis diisi dari environment variable
# (nama field versi huruf besar, mis. database_url -> DATABASE_URL) atau file .env.
# Kalau tidak ada di keduanya, dipakai nilai default di bawah.
class Settings(BaseSettings):
    # Baca dari file .env; variabel di .env yang tidak ada field-nya diabaikan (tidak error)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "todo-api"
    # Bisa diisi lewat env ENV atau ENVIRONMENT (mana saja yang ada)
    environment: str = Field(
        default="development", validation_alias=AliasChoices("ENV", "ENVIRONMENT")
    )
    port: int = 8000  # string dari env (mis. "9000") otomatis dikonversi ke int
    log_level: str = "INFO"
    database_url: str = DEFAULT_DATABASE_URL
    test_database_url: str = DEFAULT_TEST_DATABASE_URL
    # Jumlah koneksi DB yang disimpan di pool, dan tambahan maksimal saat pool penuh
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Dijalankan setelah semua field terisi & tervalidasi
    @model_validator(mode="after")
    def use_test_database(self) -> "Settings":
        """With ENV=test, always point at the test database."""
        if self.is_test:
            self.database_url = self.test_database_url
        return self

    # Helper untuk cek environment, mis. `if settings.is_production: ...`
    @property
    def is_test(self) -> bool:
        return self.environment.lower() == "test"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


# lru_cache: Settings() cukup dibuat sekali, pemanggilan berikutnya
# mengembalikan objek yang sama (tidak membaca .env berulang kali).
@lru_cache
def get_settings() -> Settings:
    return Settings()
