# webapp
This is the Karivari web app.

## Codespaces / Docker
1. Open the repository in GitHub Codespaces.
2. The included dev container will build the app from the provided Dockerfile.
3. The app runs on port 8000.

To run locally with Docker:

```bash
docker build -t karivari-webapp .
docker run --rm -p 8000:8000 karivari-webapp
```

