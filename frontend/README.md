# Wangumi Placeholder Frontend

This lightweight HTML page lets the team smoke-test the anime list and detail APIs before the real frontend lands.

## Features

- Fetch `/api/anime` with sorting / category filters.
- Display paginated cards with basic info and tags.
- Open a modal that calls `/api/anime/<id>` to show metadata, characters with voice actors, and staff.

## Getting Started

1. Ensure the Django backend is running (default `http://localhost:8000`).
2. Serve the placeholder page. Any static server works, for example:

   ```bash
   cd frontend
   python -m http.server 3000
   ```

3. Visit `http://localhost:3000` in your browser.
4. Use the controls at the top to filter or sort; click “查看详情” to inspect the detail API response. The header links jump straight to the existing backend endpoints (`/api/anime`, `/api/anime/{id}`, `/api/health`) so you can verify raw responses.

> 若后端地址不同，可在 `index.html` 的 `<script>` 之前添加：
>
> ```html
> <script>
>   window.API_BASE_URL = "https://dev.your-domain.com/api";
> </script>
> ```

## Customising

- Update `API_BASE` in `index.html` if your backend runs on a different host or prefix.
- The UI is intentionally simple. Treat it as a template for the upcoming real frontend implementation.
