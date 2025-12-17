# Use lightweight Python
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config.yaml .
COPY auth.py .
COPY main.py .

# Expose the port
EXPOSE 3455

# Run the proxy
# We use 'python -u' to unbuffer output so logs show up instantly
CMD ["python", "-u", "main.py"]