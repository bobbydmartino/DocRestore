FROM node:latest

ARG USER_ID
ARG GROUP_ID

# Create a group with the specified GID or use an existing one
RUN if getent group ${GROUP_ID}; then \
    groupmod -n dockeruser $(getent group ${GROUP_ID} | cut -d: -f1); \
  else \
    groupadd -g ${GROUP_ID} dockeruser; \
  fi

# Create a user with the specified UID/GID or modify an existing one
RUN if id -u ${USER_ID} >/dev/null 2>&1; then \
    usermod -l dockeruser -u ${USER_ID} -g ${GROUP_ID} $(id -un ${USER_ID}); \
  else \
    useradd -l -u ${USER_ID} -g ${GROUP_ID} dockeruser; \
  fi

# Set the working directory and change its ownership
WORKDIR /app
RUN chown dockeruser:dockeruser /app

# Switch to the non-root user
USER dockeruser

# Install dependencies
COPY --chown=dockeruser:dockeruser package*.json ./
RUN npm install

# Copy the rest of the application code
COPY --chown=dockeruser:dockeruser . .

CMD ["/bin/bash"]