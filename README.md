# CUJAE | Cuadro de Mando Institucional

Panel de control web para la Universidad Tecnológica de La Habana (CUJAE) que centraliza el seguimiento, cálculo y visualización de indicadores estratégicos, metas por curso académico y estados tipo semáforo (verde/amarillo/rojo) para los procesos institucionales.

---

## Arquitectura

| Servicio   | Tecnología              | Puerto |
|------------|-------------------------|--------|
| frontend   | Next.js 14 (App Router) | 3000   |
| backend    | FastAPI (Python 3.11)   | 8000   |
| db         | PostgreSQL 16           | 5432   |
| redis      | Redis 7                 | 6379   |

Todo se orquesta con Docker Compose sobre la red interna cujae_interna.

---

-- Inicio rápido

---- 1. Clonar el repositorio
Terminal de windows bash
git clone https://github.com/ArangoSharkweb/PanelDeControl_Cujae.git
cd PanelDeControl_Cujae
2. Configurar variables de entorno
bash

cp .env.example .env

Edita .env y define, como mínimo:

    POSTGRES_PASSWORD: contraseña de la base de datos.

    JWT_SECRET_KEY: secreto para firmar los tokens JWT. Genéralo con:

  Configuración

Variables clave definidas en .env.example:
Variable	Descripción
POSTGRES_PASSWORD	Contraseña de PostgreSQL. Obligatoria.
JWT_SECRET_KEY	Secreto para firmar JWT. Obligatoria.
DATABASE_URL	URL de conexión asíncrona a la base de datos.
DATABASE_URL_SYNC	URL de conexión síncrona (usada por Alembic).
REDIS_URL	URL de conexión a Redis.// por ahora no
LDAP_URL	URL del servidor LDAP institucional. // por ahora no
LDAP_BASE_DN	Base DN para búsquedas LDAP.  // por ahora no
ADMIN_INITIAL_USERNAME	Usuario del primer administrador . 
ADMIN_INITIAL_PASSWORD	Contraseña del primer administrador . 

Importante: POSTGRES_PASSWORD y JWT_SECRET_KEY son obligatorias. El sistema no arrancará sin ellas.
Estructura del proyecto
text

PanelDeControl_Cujae/
├── backend/              FastAPI + SQLAlchemy async + Alembic
│   └── app/
│       ├── api/          Routers y endpoints (/api/v1/...)
│       ├── models/       Modelos SQLAlchemy
│       ├── schemas/      Schemas Pydantic
│       ├── services/     Lógica de negocio (motor de cálculo, LDAP, etc.)
│       └── main.py       Punto de entrada FastAPI
├── frontend/             Next.js 14 (TypeScript, App Router)
│   └── src/
│       ├── app/          Rutas y páginas
│       ├── components/   Componentes reutilizables
│       ├── lib/          Clientes HTTP, validadores, utilidades
│       └── stores/       Estado global (Zustand)
├── docker-compose.yml    Orquestación de servicios
├── .env.example          Plantilla de variables de entorno
└── README.md
Desarrollo local (sin Docker)
Backend
bash

cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

Frontend
bash

cd frontend
npm install
npm run dev
