 <div align="center">
  <img
    src="assets/BatmanTaberna.png"
    alt="Demostración del Barman de la Taberna"
    width="850"
  />
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-1DB954?style=for-the-badge&logo=spotify&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)

![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square)
![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen?style=flat-square)

</div>

# Barman de la Taberna

**Un bot de Discord hecho en Python, medio borracho pero buena onda, diseñado para moderar, interactuar con miembros y ejecutar música en los canales de voz.**

Barman de la Taberna es un proyecto enfocado actualmente en la reproducción de música desde YouTube, con integración de Spotify para obtener información de las canciones y encontrarlas en YouTube.

Está hecho con `discord.py`, `yt-dlp`, `spotipy` y `FFmpeg`. El proyecto se enfoca en una arquitectura limpia, operaciones asíncronas y una experiencia de música inolvidable.

# Características del Bot

- **Motor de YouTube**: Reproduce canciones desde URLs de YouTube o del mismo motor de búsqueda de YouTube.
- **Integración de Spotify**: Resuelve URLs y URIs de las canciones de Spotify, recuperando la metadata y encontrando la canción con el motor de YouTube.
- **Embeds facheros**: Muestra el título de la canción, artista, artwork del álbum, duración formateada y link de la canción.
- **Canal de voz soportado**: Conecta el bot a cualquier canal de voz de cualquier servidor donde **este mismo esté activo**.
- **Extracción asíncrona**: Realiza la extracción de metadatos bloqueantes fuera del bucle de eventos de Discord.
- **Manejo de errores**: Se manejan las extracciones fallidas, como también los errores de los motores.

# Comandos

| Comando | Descripción | Parámetro |
| ------- | ----------- | --------- |
| `/join` | Conecta el bot a un canal de voz específico. | `channel` |
| `/play` | Reproducí cualquier canción de YouTube o un link de Spotify. | `cancion` |
| `/stop` | Detiene la reproducción y desconecta al bot. | Ninguno |

# Tecnologías

| Tecnología | Propósito |
| ---------- | --------- |
| Python | Lenguaje de programación elegido. |
| discord.py | Integración con la API de Discord y reproducción de voz. |
| yt-dlp | Extracción de fuentes de audio. |
| spotipy | Integración de metadatos de Spotify. |
| FFmpeg | Decodificación y transmisión de audio. |
| asyncio | Operaciones asíncronas. |

# Preparando el entorno del Bot [Instalación y Pre-requisitos]

Antes de intentar ejecutar el bot, tenemos que estar seguros de algunas cosas:

### Pre-requisitos

- `Python`: Lo tenés que tener instalado. Si no lo tenés, descargá el ejecutable en su página:

  [Descargar Python](https://www.python.org/downloads/)

- `FFmpeg`: Tiene que estar **sí o sí** instalado. Si no lo tenés, podés descargarlo acá:

  [Descargar FFmpeg](https://ffmpeg.org/download.html)

Si querés saber cómo instalar FFmpeg, te recomiendo estos tutoriales:

**Windows**: [Tutorial de instalación](https://www.youtube.com/watch?v=KBnyOH1o5Ms)

**Linux**: [Tutorial de instalación](https://www.youtube.com/watch?v=ieY22NE0N7o)

**macOS**: [Tutorial de instalación](https://www.youtube.com/watch?v=KAMuQTmGJUI)

> [!IMPORTANT]
> FFmpeg tiene que estar disponible en el `PATH` de tu sistema operativo para que el bot pueda utilizarlo.

Podés verificar la instalación ejecutando:

```bash
ffmpeg -version
```

- Necesitás, por otro lado, una aplicación de Discord y un **token** para tu bot.
- Credenciales API para Spotify (Web API).

### Cloná el repositorio

Vas a necesitar clonar el repositorio:

```bash
git clone https://github.com/rodrigorierafiuba/barman-taberna-bot.git
```

Después andá a la raíz del proyecto:

```bash
cd barman-taberna-bot
```

### Instalá las dependencias

Este proyecto utiliza [uv](https://docs.astral.sh/uv/), y recomiendo fuertemente que lo uses. Ya sé que hay gente que está acostumbrada capaz a utilizar `pip`, pero sinceramente `uv` te cambia la vida y es muy simple de utilizar a lo largo del proyecto.

- Te recomiendo instalar `uv` acá:

  [Documentación e Instalación de uv](https://docs.astral.sh/uv/getting-started/installation/)

Para sincronizar las librerías utilizadas del proyecto, corré el siguiente comando:

```bash
uv sync
```

### Configurá las variables de entorno

> [!IMPORTANT]
> Configurá el token de tu bot de Discord y las credenciales de Spotify usando un archivo `.env`.

Las variables que tendrías que utilizar son las siguientes:

```dotenv
DISCORD_TOKEN=tu_token_de_discord
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
```

> [!WARNING]
> Nunca subas el `.env` a un repositorio! La solución es incluirlo en el `.gitignore`.

### Corré el bot

Para correr el bot, ejecutá el siguiente comando:

```bash
uv run python -m discord_bot.bot
```

Una vez conectado el bot, vas a ver que es medio borracho pero buena onda. Podés invitarlo a tu servidor de Discord y usar los comandos disponibles hasta la última versión estable de este repositorio.

## Arquitectura

El proyecto separa lo que son los comandos de Discord de las fuentes de audio para manejar la música.

<div align="center">
  <img
    src="assets/funcionamiento_bot.png"
    alt="Diagrama de flujo de funcionamiento del bot."
    width="850"
  />
</div>

**SpotifySource**: Maneja el flujo de reconocimiento de las canciones proporcionadas por URL o URI y se ocupa de conseguir y guardar en **`SpotifyTrack`** la metadata de la canción.

**SpotifyTrack**: Guarda la metadata conseguida por **`SpotifySource`**.

**YTDLSource**: Extrae información de audio, prepara las fuentes de audio de FFmpeg y gestiona los metadatos de reproducción.

**Music Cog**: Maneja las interacciones con Discord y coordina la reproducción de música.

> [!NOTE]
> Spotify se utiliza para obtener la metadata de las canciones. El audio reproducido por el bot se obtiene mediante YouTube y se procesa utilizando `yt-dlp` y FFmpeg.

## Hoja de ruta

Las siguientes funcionalidades están previstas para futuras versiones:

- [ ] Soporte de listas de reproducción.
- [ ] Sistema de cola musical.
- [ ] Comando `/skip`.
- [ ] Modificar `/stop` para detener la reproducción sin desconectarse.
- [ ] Comando `/disconnect`.
- [ ] Integración con proveedores musicales adicionales [En revisión, pero posible].
- [ ] Mejor manejo de videos restringidos o no disponibles.
- [ ] Mejoras en la recuperación de errores.

El progreso del proyecto se organizará mediante GitHub Issues, Pull Requests y Milestones.

## Contribuciones

Las contribuciones por el momento están cerradas, pero cualquier sugerencia o reporte de bug es bienvenido.

Si encontrás un problema o tenés una idea para una nueva característica, sentite libre de generar un **Issue**.

## Licencia

La información de la licencia va a ser agregada una vez que haya sido seleccionada.

---

Hecho con mucha pasión y café, **Rodrigo** ☕🍻