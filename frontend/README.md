# React dashboard

This is the source for the AI-Powered MySQL Testing Framework dashboard. The
Python server in `../gui_dashboard.py` provides the API; Vite provides the
React interface.

## Development

In one terminal, start the API server from the project root:

```bash
python gui_dashboard.py
```

In another terminal, start Vite:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). Requests to
`/api`, report images, and report files are proxied to the Python server on
port 8050.

## Production / local dashboard

Build the React application, then run the Python server:

```bash
cd frontend
npm run build
cd ..
python gui_dashboard.py
```

The build is written to `../dashboard`, which `gui_dashboard.py` serves at
`http://localhost:8050`. Do not delete `dashboard/index.html` or
`dashboard/assets/`: they are the compiled React application. The previous
single-file HTML dashboard has been retired.
