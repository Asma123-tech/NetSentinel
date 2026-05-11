# ─────────────────────────────────────────────
# Nginx container for NetSentinel
# Uses the official lightweight nginx image
# ─────────────────────────────────────────────

FROM nginx:alpine

# Remove the default nginx config
RUN rm /etc/nginx/nginx.conf

# Copy our custom config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80 to the outside world
EXPOSE 80

# Start Nginx in the foreground (required for Docker)
CMD ["nginx", "-g", "daemon off;"]