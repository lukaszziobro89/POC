# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Install uv globally in the builder stage for easier use
# Use python -m pip to ensure it uses the correct pip for the base python
RUN python -m pip install --no-cache-dir --upgrade pip uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Create venv using the global uv, then sync dependencies into it using the global uv
# Explicitly point to the python interpreter inside the venv for the sync target
RUN uv venv /app/venv && \
    uv sync --python /app/venv/bin/python

# Stage 2: Runtime image
FROM python:3.10-slim

WORKDIR /app

# Create a non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup --disabled-password --gecos "" appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv /app/venv

# Copy application code (set ownership during copy)
COPY --chown=appuser:appgroup . .

# Set environment variables to use the venv
# The warning about $PYTHONPATH is usually safe to ignore here.
ENV PATH="/app/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV="/app/venv"

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]