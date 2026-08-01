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


def test_database_url_whitespace_is_collapsed() -> None:
    """A secret pasted with an embedded newline must not corrupt sslmode.

    Reproduces the failure where a multiline-tainted ``DATABASE_URL`` yielded
    ``sslmode=require\\n`` and libpq rejected it as "invalid sslmode value".
    """
    tainted = "  postgresql+psycopg://u:p@host/db?sslmode=require\n&channel_binding=require  "
    settings = Settings(database_url=tainted)
    assert "\n" not in settings.database_url
    assert " " not in settings.database_url
    assert (
        settings.database_url
        == "postgresql+psycopg://u:p@host/db?sslmode=require&channel_binding=require"
    )


def test_blank_smtp_port_falls_back_to_default() -> None:
    settings = Settings(smtp_port="")
    assert settings.smtp_port == 465


def test_bare_postgres_url_gets_psycopg_driver() -> None:
    """Railway/Neon emit driver-less URLs; SQLAlchemy would pick psycopg2."""
    for scheme in ("postgresql", "postgres"):
        settings = Settings(database_url=f"{scheme}://u:p@host/db?sslmode=require")
        assert settings.database_url == ("postgresql+psycopg://u:p@host/db?sslmode=require")


def test_explicit_driver_url_is_left_untouched() -> None:
    url = "postgresql+psycopg://u:p@host/db?sslmode=require"
    assert Settings(database_url=url).database_url == url
