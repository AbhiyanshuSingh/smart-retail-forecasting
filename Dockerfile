# # Use official Python slim image
# FROM python:3.10-slim

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1

# # Install dependencies for LightGBM
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgomp1 \
#  && rm -rf /var/lib/apt/lists/*

# # System deps (curl/tar for azcopy)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#       ca-certificates curl tar \
#     && rm -rf /var/lib/apt/lists/*


# # Install AzCopy (for recursive folder download with SAS)
# # aka.ms link always points to latest v10 tarball
# RUN curl -sSL https://aka.ms/downloadazcopy-v10-linux -o /tmp/azcopy.tgz \
#     && tar -xzf /tmp/azcopy.tgz -C /tmp \
#     && cp /tmp/azcopy_linux_amd64_*/azcopy /usr/local/bin/ \
#     && chmod +x /usr/local/bin/azcopy \
#     && rm -rf /tmp/azcopy*

# # Set working directory
# WORKDIR /app

# # Copy requirements file first for better caching
# COPY requirements.txt .

# # Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy all project files
# COPY . .

# # Add entrypoint script
# COPY entrypoint.sh /app/entrypoint.sh
# RUN chmod +x /app/entrypoint.sh

# # Expose port for FastAPI
# EXPOSE 8000

# # # Start FastAPI server
# # CMD ["uvicorn", "app_nolag:app", "--host", "0.0.0.0", "--port", "8000"]

# # Use the entrypoint to pull data & start Uvicorn
# ENTRYPOINT ["/app/entrypoint.sh"]







############################################################################################

FROM python:3.10-slim

# Install system dependencies (add libgomp1 for LightGBM)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    curl \
    unzip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (exclude local data)
COPY . .

COPY data ./data

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# # Use the entrypoint that downloads data from GitHub Releases
ENV APP_MODULE=app_nolag:app
EXPOSE 8080
# CMD ["/bin/bash", "/app/entrypoint.sh"]

# Run entrypoint
CMD ["/app/entrypoint.sh"]