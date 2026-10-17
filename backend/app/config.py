from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://crm:crm@localhost:5432/crm_oftalmo"
    admin_token: str = "gabriel"
    tz: str = "America/Argentina/Buenos_Aires"
    seed_demo: bool = True

    # Datos del consultorio
    nombre_consultorio: str = "Labatte Oftalmología"
    direccion: str = "Av. Siempre Viva 742"
    telefono_contacto: str = ""
    horario_texto: str = "Lunes a viernes de 9 a 13 y de 15 a 19 hs"
    info_extra: str = ""

    # Agenda
    franjas_horarias: str = "09:00-13:00,15:00-19:00"
    dias_laborales: str = "0,1,2,3,4"
    duracion_turno_min: int = 20
    anticipacion_min_horas: int = 2
    dias_a_ofrecer: int = 5
    max_turnos_dia: int = 5  # 0 = sin límite

    # WhatsApp Cloud API
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_verify_token: str = "cambiar-verify-token"
    whatsapp_app_secret: str = ""
    whatsapp_api_version: str = "v21.0"

    @property
    def dias_laborales_set(self) -> set[int]:
        return {int(d) for d in self.dias_laborales.split(",") if d.strip()}

    @property
    def whatsapp_activo(self) -> bool:
        return bool(self.whatsapp_token and self.whatsapp_phone_id)


settings = Settings()
