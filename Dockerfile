FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/agentshield /app/src/agentshield

RUN pip install .

EXPOSE 8000

CMD ["agentshield", "serve"]