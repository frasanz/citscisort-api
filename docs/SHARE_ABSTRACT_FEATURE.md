# Funcionalidad de Compartir Abstracts por Email

## Resumen
Los usuarios pueden compartir abstracts interesantes por email con otras personas, incluyendo un mensaje personalizado.

## API Endpoints

### 1. Compartir un abstract
**POST** `/api/abstracts/{id}/share/`

Envía un abstract por email a un destinatario.

**Autenticación**: Requerida

**Request Body**:
```json
{
  "recipient_email": "usuario@example.com",
  "message": "¡Mira este abstract interesante sobre citizen science!" 
}
```

**Parámetros**:
- `recipient_email` (string, requerido): Email del destinatario
- `message` (string, opcional): Mensaje personalizado del remitente (max 1000 caracteres)

**Response Success (200)**:
```json
{
  "success": true,
  "message": "Abstract shared successfully with usuario@example.com",
  "shared_id": 123,
  "shared_at": "2025-11-13T15:30:00Z"
}
```

**Response Error (500)**:
```json
{
  "success": false,
  "error": "Failed to send email. Please try again later."
}
```

**Ejemplo de uso**:
```javascript
const response = await fetch(`/api/abstracts/456/share/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Token your-auth-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    recipient_email: 'colleague@university.edu',
    message: 'This paper might be relevant for our project!'
  })
});
```

---

### 2. Ver mis abstracts compartidos
**GET** `/api/abstracts/my_shared/`

Obtiene el historial de abstracts que el usuario ha compartido (últimos 50).

**Autenticación**: Requerida

**Response (200)**:
```json
{
  "shared_abstracts": [
    {
      "id": 123,
      "abstract_id": 456,
      "abstract_title": "Citizen Science in Environmental Monitoring",
      "recipient_email": "usuario@example.com",
      "message": "Check this out!",
      "shared_at": "2025-11-13T15:30:00Z",
      "email_sent_successfully": true
    }
  ],
  "total": 5
}
```

---

### 3. Abstracts más compartidos (estadísticas)
**GET** `/api/abstracts/most_shared/?limit=10`

Obtiene los abstracts más compartidos por la comunidad (estadísticas anónimas).

**Autenticación**: Requerida

**Query Parameters**:
- `limit` (integer, opcional): Número de resultados (default: 10)

**Response (200)**:
```json
{
  "most_shared": [
    {
      "id": 456,
      "title": "Citizen Science in Environmental Monitoring",
      "authors": "Smith, J. et al.",
      "year": 2024,
      "shares_count": 25
    }
  ],
  "note": "Anonymous community statistics - shows how many times each abstract was shared"
}
```

---

## Modelo de Datos: SharedAbstract

```python
class SharedAbstract(models.Model):
    user = ForeignKey(User)  # Usuario que comparte
    abstract = ForeignKey(Abstract)  # Abstract compartido
    recipient_email = EmailField()  # Email del destinatario
    message = TextField()  # Mensaje personalizado
    shared_at = DateTimeField()  # Fecha de envío
    email_sent_successfully = BooleanField()  # Si el email se envió correctamente
```

---

## Email Template

El email enviado incluye:
- Nombre del remitente
- Mensaje personalizado (si se proporciona)
- Título del abstract
- Autores
- Año de publicación
- Journal
- DOI
- Texto del abstract (primeros 500 caracteres)
- Keywords
- Link al abstract completo

---

## Configuración de Email

El sistema usa **Amazon SES** configurado en `settings.py`:

```python
EMAIL_BACKEND = 'django_ses.SESBackend'
DEFAULT_FROM_EMAIL = 'noreply@whatcitsiawedo.com'
AWS_SES_REGION_ENDPOINT = 'email.eu-central-1.amazonaws.com'
```

Las credenciales de AWS se configuran mediante variables de entorno en `.env`:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SES_REGION_ENDPOINT`

---

## Frontend Implementation Example

### Botón de Compartir en Card de Abstract

```tsx
import { useState } from 'react';
import { ShareIcon } from '@heroicons/react/24/outline';

function AbstractCard({ abstract }) {
  const [showShareModal, setShowShareModal] = useState(false);
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleShare = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`/api/abstracts/${abstract.id}/share/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recipient_email: email,
          message: message
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('Abstract shared successfully!');
        setShowShareModal(false);
        setEmail('');
        setMessage('');
      } else {
        alert('Failed to share: ' + data.error);
      }
    } catch (error) {
      alert('Error sharing abstract');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="abstract-card">
      <h3>{abstract.title}</h3>
      <p>{abstract.authors}</p>
      
      <div className="actions">
        <button onClick={() => setShowShareModal(true)}>
          <ShareIcon className="w-5 h-5" />
          Share
        </button>
      </div>

      {showShareModal && (
        <ShareModal
          onClose={() => setShowShareModal(false)}
          email={email}
          setEmail={setEmail}
          message={message}
          setMessage={setMessage}
          onSubmit={handleShare}
          loading={loading}
        />
      )}
    </div>
  );
}
```

---

## Validaciones

1. **Email válido**: Se valida formato de email
2. **Abstract existe**: Se verifica que el abstract esté activo
3. **Mensaje opcional**: Max 1000 caracteres
4. **Tracking**: Todos los intentos se guardan en BD (exitosos o fallidos)

---

## Seguridad y Privacidad

- ✅ Requiere autenticación
- ✅ No expone emails de otros usuarios
- ✅ No hay límite de rate-limiting implementado (considerar añadir)
- ✅ Se guarda historial para prevenir spam
- ⚠️ **Recomendación**: Añadir rate limiting (ej: máximo 10 emails por hora por usuario)

---

## Testing

Para probar en desarrollo, configura en `.env`:

```bash
# Para testing local con console backend
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Para testing real con SES
EMAIL_BACKEND=django_ses.SESBackend
DEFAULT_FROM_EMAIL=noreply@whatcitsiawedo.com
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_SES_REGION_ENDPOINT=email.eu-central-1.amazonaws.com
```

---

## Django Admin

El modelo `SharedAbstract` está registrado en Django Admin con vista de solo lectura:

- Lista de abstracts compartidos
- Filtros por fecha y éxito de envío
- Búsqueda por usuario, destinatario y título
- No permite crear/editar manualmente (solo lectura)

---

## Posibles Mejoras Futuras

1. **Rate Limiting**: Limitar número de emails por usuario/hora
2. **Templates HTML**: Crear templates HTML profesionales para emails
3. **Unsubscribe link**: Añadir link de unsubscribe en emails
4. **Analytics**: Dashboard de abstracts más compartidos
5. **Social sharing**: Añadir botones para compartir en Twitter/LinkedIn
6. **Email verification**: Verificar que el email del destinatario es válido
7. **BCC copy**: Opción de enviar copia al remitente
8. **Scheduled sharing**: Programar envío para fecha futura
