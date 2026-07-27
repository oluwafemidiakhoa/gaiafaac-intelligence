from gaiafaac_api.config import Settings


def test_blank_env_vars_fall_back_to_defaults() -> None:
    settings = Settings(api_environment="", api_host="", database_url="")
    assert settings.api_environment == "development"
    assert settings.api_host == "0.0.0.0"
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_whitespace_env_var_falls_back_to_default() -> None:
    settings = Settings(api_environment="   ")
    assert settings.api_environment == "development"


def test_real_values_pass_through() -> None:
    settings = Settings(api_environment="production", api_host="127.0.0.1")
    assert settings.api_environment == "production"
    assert settings.api_host == "127.0.0.1"
