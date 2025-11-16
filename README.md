# CitSciSort API

Backend API for the citizen science classification platform CitSciSort, built with Django REST Framework.

## Características

- 🔐 Autenticación completa con dj-rest-auth
- 📧 Verificación de email con Amazon SES
- 🗄️ Base de datos PostgreSQL
- 🔑 Gestión segura de variables de entorno
- 🌐 API RESTful con Django REST Framework

## Requisitos Previos

- Python 3.10 o superior
- PostgreSQL 14 o superior
- Cuenta de AWS con SES configurado (para envío de emails)

## Instalación

1. **Clonar el repositorio y navegar al directorio**

```bash
cd citscisort-api
```

2. **Crear y activar un entorno virtual**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

Copia el archivo `.env.example` a `.env` y configura tus variables:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales reales:
- Configura las credenciales de PostgreSQL
- Añade tus credenciales de AWS SES
- Genera una SECRET_KEY segura para Django

5. **Crear la base de datos PostgreSQL**

```bash
psql -U postgres
CREATE DATABASE citscisort_db;
\q
```

6. **Ejecutar migraciones**

```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Crear un superusuario**

```bash
python manage.py createsuperuser
```

8. **Ejecutar el servidor de desarrollo**

```bash
python manage.py runserver
```

La API estará disponible en `http://localhost:8000`

## Endpoints de Autenticación

Los siguientes endpoints están disponibles para la autenticación:

### Registro y Login

- `POST /api/auth/registration/` - Registro de nuevo usuario
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/user/` - Obtener usuario actual
- `PUT/PATCH /api/auth/user/` - Actualizar usuario actual

### Gestión de Contraseña

- `POST /api/auth/password/reset/` - Solicitar reset de contraseña
- `POST /api/auth/password/reset/confirm/` - Confirmar reset de contraseña
- `POST /api/auth/password/change/` - Cambiar contraseña (requiere autenticación)

### Verificación de Email

- `POST /api/auth/registration/verify-email/` - Verificar email
- `POST /api/auth/registration/resend-email/` - Reenviar email de verificación

## Configuración de Amazon SES

Para configurar Amazon SES:

1. Accede a la consola de AWS SES
2. Verifica tu dominio o dirección de email
3. Crea credenciales IAM con permisos de SES
4. Configura las credenciales en tu archivo `.env`

## Estructura del Proyecto

```
citscisort-api/
├── apps/
│   ├── authentication/      # App de autenticación
│   └── __init__.py
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py         # Configuración principal
│   ├── urls.py             # URLs principales
│   └── wsgi.py
├── .env.example            # Plantilla de variables de entorno
├── .gitignore
├── manage.py
├── README.md
└── requirements.txt
```

## Próximos Pasos

- [ ] Definir modelos de datos para proyectos de ciencia ciudadana
- [ ] Implementar endpoints para CRUD de proyectos
- [ ] Añadir permisos y roles de usuario
- [ ] Implementar sistema de contribuciones

## 🔒 Seguridad

Antes de hacer commit al repositorio, ejecuta el script de verificación de seguridad:

```bash
./check-security.sh
```

Este script verifica:
- ✅ Que `.env` no esté trackeado
- ✅ No hay claves privadas (`.pem`, `.key`)
- ✅ No hay credenciales hardcodeadas
- ✅ No hay archivos de logs
- ✅ No hay dumps de base de datos

Para más información sobre seguridad, consulta [SECURITY.md](./SECURITY.md)

## 📄 Licencia

Este proyecto está licenciado bajo la **European Union Public Licence (EUPL) v1.2**.

La EUPL es una licencia copyleft compatible con otras licencias principales de código abierto como GPL, AGPL, y MPL.

Ver el archivo [LICENSE](./LICENSE) para más detalles.

### ¿Por qué EUPL?

- ✅ **Copyleft fuerte**: Garantiza que el software derivado permanezca libre
- ✅ **Compatible**: Compatible con GPL, AGPL, MPL y otras licencias populares
- ✅ **Multilingüe**: Disponible en todos los idiomas oficiales de la UE
- ✅ **Europea**: Creada específicamente para el contexto legal europeo

## Contacto

[Por definir]
