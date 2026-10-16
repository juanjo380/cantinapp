# CantinAPP Backend

## Desarrolladores

<p align="center">
  <a href="https://github.com/JuanRuiz1012" target="_blank">
    <img src="https://github.com/JuanRuiz1012.png?size=100" alt="Foto de Perfil de Juan Ruiz" width="100" height="100" style="border-radius: 50%;">
  </a>
  <br>
  <b>Juan Ruiz - 2359397</b>
  <br>
  <a href="https://github.com/JuanRuiz1012" target="_blank">
    @JuanRuiz1012
  </a>
</p>

--- <p align="center">
  <a href="https://github.com/juanjo380" target="_blank">
    <img src="https://github.com/juanjo380.png?size=100" alt="Foto de Perfil de juanjo380" width="100" height="100" style="border-radius: 50%;">
  </a>
  <br>
  <b>Juan Bolaños - 2380616</b>
  <br>
  <a href="https://github.com/juanjo380" target="_blank">
    @juanjo380
  </a>
</p>

--- <p align="center">
  <a href="https://github.com/juanjounivalle18" target="_blank">
    <img src="https://github.com/juanjounivalle18.png?size=100" alt="Foto de Perfil de juanjounivalle18" width="100" height="100" style="border-radius: 50%;">
  </a>
  <br>
  <b>Juan José Millan - 2266393</b>
  <br>
  <a href="https://github.com/juanjounivalle18" target="_blank">
    @juanjounivalle18
  </a>
</p>

--- <p align="center">
  <a href="https://github.com/JulianAndresRojasPalacio" target="_blank">
    <img src="https://github.com/JulianAndresRojasPalacio.png?size=100" alt="Foto de Perfil de JulianAndresRojasPalacio" width="100" height="100" style="border-radius: 50%;">
  </a>
  <br>
  <b>Julian Rojas - 2459687</b>
  <br>
  <a href="https://github.com/JulianAndresRojasPalacio" target="_blank">
    @JulianAndresRojasPalacio
  </a>
</p>

--- <p align="center">
  <a href="https://github.com/DanielCamelo" target="_blank">
    <img src="https://github.com/DanielCamelo.png?size=100" alt="Foto de Perfil de DanielCamelo" width="100" height="100" style="border-radius: 50%;">
  </a>
  <br>
  <b>Daniel Camelo - 2477171</b>
  <br>
  <a href="https://github.com/JulianAndresRojasPalacio" target="_blank">
    @DanielCamelo
  </a>
</p>


## Requisitos

- Python instalado y disponible como `py`.
- Una base de datos PostgreSQL en Supabase.

## Instalación en Windows PowerShell

Abre PowerShell y ejecuta:

```powershell
cd "C:\Users\USUARIO\Desktop\cantinapp\backend"
```

### Crear el entorno virtual

```powershell
py -m venv .venv
```

### Activar el entorno virtual

Si PowerShell bloquea la ejecución de scripts, ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después activa el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

La terminal debe mostrar `(.venv)` al inicio de la línea.

### Actualizar pip e instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuración del archivo `.env`

Crea el archivo:

```text
C:\Users\USUARIO\Desktop\cantinapp\backend\.env
```

Agrega el siguiente contenido y reemplaza los valores de Supabase:

```env
APP_NAME=CantinAPP API
ENVIRONMENT=development

DB_HOST=tu-host-de-supabase
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu-password-de-supabase

DB_SSL=true
DB_USE_TRANSACTION_POOLER=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_ECHO=false

JWT_SECRET=cambia-este-secreto-en-produccion
JWT_EXPIRE_MINUTES=720
CORS_ORIGINS=["http://localhost:5173"]
```

El esquema de la base de datos está en [`../db/schema.sql`](../db/schema.sql). Ejecútalo en el **SQL Editor de Supabase** antes de iniciar la API.

## Levantar el backend

Con el entorno virtual activo y ubicado en la carpeta `backend`, ejecuta:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

Documentación interactiva de FastAPI:

```text
http://127.0.0.1:8000/docs
```

## Comprobar que la API funciona

En otra terminal de PowerShell:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

Para comprobar también la conexión con la base de datos:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health/db
```

## Levantar el proyecto después de la instalación

Cada vez que quieras iniciar el backend:

```powershell
cd "C:\Users\USUARIO\Desktop\cantinapp\backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Detener el backend

En la terminal donde está ejecutándose Uvicorn, presiona:

```text
Ctrl + C
```

Para salir del entorno virtual:

```powershell
deactivate
```
