FROM python:3.9-slim

ARG USER_ID
ARG GROUP_ID

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create a group and user
RUN groupadd -g ${GROUP_ID} dockeruser && \
    useradd -u ${USER_ID} -g dockeruser -m -s /bin/bash dockeruser

# Set the working directory
WORKDIR /app

# Create log file and set permissions
RUN touch /var/log/pdf_processor.log && \
    chown dockeruser:dockeruser /var/log/pdf_processor.log

# Change ownership of the app directory
RUN chown -R dockeruser:dockeruser /app

# Switch to the non-root user
USER dockeruser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["python", "app.py"]