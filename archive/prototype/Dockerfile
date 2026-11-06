FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=60s --timeout=5s --start-period=10s \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"
CMD ["python3", "server.py", "8000"]
