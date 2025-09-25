# Dockerfile cho Fabric Endpoint Service
FROM ubuntu:22.04

# Cài đặt dependencies hệ thống
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Go để build Fabric
RUN wget https://go.dev/dl/go1.23.1.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.23.1.linux-amd64.tar.gz && \
    rm go1.23.1.linux-amd64.tar.gz

# Thêm Go vào PATH
ENV PATH="/usr/local/go/bin:${PATH}"

# Tạo user cho application
RUN useradd -m -s /bin/bash fabricuser
USER fabricuser
WORKDIR /home/fabricuser

# Cài đặt Fabric từ Go source - sử dụng đường dẫn cmd đúng
RUN go install github.com/danielmiessler/fabric/cmd/fabric@latest

# Thêm Go bin vào PATH cho fabricuser
ENV PATH="/home/fabricuser/go/bin:${PATH}"

# Chuyển về root để copy files và cài đặt Python packages
USER root

# Tạo thư mục app
WORKDIR /app

# Copy requirements và cài đặt Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy service code
COPY fabric_service.py .

# Tạo script để setup Fabric
COPY <<EOF /app/setup_fabric.sh
#!/bin/bash
set -e

echo "Setting up Fabric configuration..."

# Tạo thư mục config cho Fabric
mkdir -p /home/fabricuser/.config/fabric

# Tạo file config cơ bản
cat > /home/fabricuser/.config/fabric/config.yaml << 'YAML'
# Fabric Configuration
model: gpt-4o
temperature: 0.7
stream: true
topp: 0.95
presencepenalty: 0.1
frequencypenalty: 0.2
YAML

# Set ownership
chown -R fabricuser:fabricuser /home/fabricuser/.config

# Chạy fabric setup nếu có biến môi trường API keys
if [ ! -z "\$OPENAI_API_KEY" ] || [ ! -z "\$ANTHROPIC_API_KEY" ]; then
    echo "Running fabric setup with provided API keys..."
    sudo -u fabricuser bash -c "cd /home/fabricuser && fabric --setup" || true
fi

echo "Fabric setup completed!"
EOF

RUN chmod +x /app/setup_fabric.sh

# Tạo startup script
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "Starting Fabric Endpoint Service..."

# Setup Fabric
/app/setup_fabric.sh

# Start the Python service
exec python3 /app/fabric_service.py
EOF

RUN chmod +x /app/start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/fabricuser/go/bin:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose port
EXPOSE 8081

# Start the service
CMD ["/app/start.sh"]
