FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy the entire project
COPY . .

# Install dependencies using uv's native commands
RUN uv sync
RUN . .venv/bin/activate

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application with uvicorn server
CMD ["uv", "run", "python3", "main.py"]