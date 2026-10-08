# NoteTaker

A Flask and SQLite note-taking application with CRUD operations, search, auto-save, and OpenRouter-powered translation.

## Features

- Create, edit, save, search, and delete notes.
- Auto-save existing notes two seconds after editing.
- Translate a note title and content into Chinese (simplified), Chinese (traditional), English, Japanese, Korean, or Spanish.
- Attach images and common documents to saved notes.
- User accounts with hashed passwords and private notes.
- Responsive browser interface.

## Project Structure

```text
MyNoteTaking/
|- src/
|  |- main.py              Flask application entry point
|  |- translator.py        OpenRouter translation client
|  |- models/              SQLAlchemy models
|  |- routes/              Flask API blueprints
|  `- static/index.html     Browser application
|- database/app.db         Local SQLite database, created automatically
|- requirements.txt         Python dependencies
|- .env                    Local credentials, ignored by Git
`- README.md
```

## Setup Tutorial

### 1. Create the Conda environment

From the project root:

```powershell
conda create --name COMP5241 python=3.11 pip --yes
conda activate COMP5241
```

If the environment already exists, only run `conda activate COMP5241`.

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure OpenRouter

Create `.env` in the project root. Never commit this file or place the API key in frontend code.

```dotenv
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
```

The repository already ignores `.env` through `.gitignore`.

### 4. Start the application

Run this command from the project root:

```powershell
python src/main.py
```

Open `http://localhost:5001` in a browser.

## Account Tutorial

1. Create an account with a username, email, and password of at least eight characters.
2. Sign in with the username and password.
3. Only notes belonging to the signed-in account are returned by the API and shown in the sidebar.
4. Use **Log out** before another person signs in on the same browser.

Passwords are stored as one-way Werkzeug password hashes. The application never stores or returns a plaintext password.

## Translation Tutorial

1. Select an existing note or click **New Note**.
2. Enter a title and content.
3. Select the target language beside the **Translate** button.
4. Click **Translate**.
5. Check the translated title and content in the editor.
6. Click **Save** to persist the translated note.

## Attachment Tutorial

1. Save the note first. New notes must have an ID before a file can be attached.
2. Choose an image or document in the **Attachments** section.
3. Click **Attach**.
4. Click an attached filename to open it, or click `x` to remove it.

Supported types include common images, PDF, Word, Markdown, text, Excel, and ZIP files. Each upload is limited to 10 MB and is stored under the local `uploads` directory.

The browser sends the text to Flask at `/api/translate`. The server reads the OpenRouter key from `.env`, calls the configured model in `src/translator.py`, and returns JSON containing `title` and `content`. The key is never sent to the browser.

## API Endpoints

### Notes

- `GET /api/notes` - List notes, newest updated first.
- `POST /api/notes` - Create a note with `title` and `content`.
- `GET /api/notes/<id>` - Get one note.
- `PUT /api/notes/<id>` - Update a note.
- `DELETE /api/notes/<id>` - Delete a note.
- `GET /api/notes/search?q=<query>` - Search note titles and content.
- `POST /api/notes/<id>/attachments` - Upload an image or document using multipart field `file`.
- `GET /api/attachments/<id>` - Open an attachment.
- `DELETE /api/attachments/<id>` - Delete an attachment.

### Authentication

- `POST /api/auth/register` - Create an account and sign in.
- `POST /api/auth/login` - Start a session.
- `GET /api/auth/me` - Get the current account.
- `POST /api/auth/logout` - End the current session.

### Translation

`POST /api/translate`

Request:

```json
{
  "title": "Prepare BBQ",
  "content": "Pork\nChicken\nVegetables",
  "target_language": "Chinese (traditional)"
}
```

Response:

```json
{
  "title": "translated title",
  "content": "translated content"
}
```

The actual response depends on the LLM. Invalid language selections and empty notes return `400`. OpenRouter or translation failures return `502`.

## Database

The app creates the local SQLite database and tables automatically on startup. Existing notes without an owner are assigned to the first account registered after authentication is enabled.

## Neon Cloud Database

Neon is a hosted PostgreSQL database. The Flask application already supports it through `DATABASE_URL`.

1. Create a project and database in Neon.
2. Copy the pooled connection string from Neon. It normally starts with `postgresql://` and includes `sslmode=require`.
3. Add it to `.env` without committing the file:

```dotenv
SECRET_KEY=use-a-long-random-value
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

4. Install dependencies and start the app:

```powershell
python -m pip install -r requirements.txt
python src/main.py
```

The `psycopg` driver connects SQLAlchemy to Neon, and the tables are created on startup for this coursework app. For production, use Alembic migrations instead of relying on `db.create_all()`.

Neon stores users, notes, and attachment metadata. The current attachment files are stored on the local disk under `uploads`, so a deployed server may lose them after restart. For production attachments, store the files in object storage such as S3, Cloudflare R2, or Supabase Storage and keep only the URL and metadata in Neon.

## Troubleshooting

- `OPENROUTER_API_KEY is not configured`: Check that `.env` is in the project root and that the environment is active.
- `401 Authentication required`: Sign in or register before loading notes.
- `SECRET_KEY` warning: Set a long random `SECRET_KEY` in `.env` before deployment.
- Neon connection errors: Verify `DATABASE_URL`, `sslmode=require`, and that the `psycopg` dependency is installed.
- Translation fails with an API error: Check the API key, model availability, network connection, and OpenRouter limits.
- The browser cannot connect: Confirm that `python src/main.py` is still running and use `http://localhost:5001`.
- `ModuleNotFoundError`: Activate `COMP5241`, then run `python -m pip install -r requirements.txt` again.
- Existing notes are missing after moving the project: Copy `database/app.db` with the project.
- Attachments are missing after moving the project: Copy the `uploads` directory with `database/app.db`.

## Verification

Compile the Python modules and run a local smoke test:

```powershell
python -m py_compile src/main.py src/translator.py src/routes/note.py
python -c "from src.main import app; print(app.test_client().get('/').status_code)"
```
