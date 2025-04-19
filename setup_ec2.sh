#!/bin/bash

# Exit on error
set -e

echo "Starting setup..."

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
echo "Installing Python and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv ~/venv
source ~/venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install streamlit pandas numpy plotly pymysql boto3 python-dotenv

# Create app directory and copy files
echo "Setting up application directory..."
mkdir -p ~/finance-analyzer
cd ~/finance-analyzer
cp ~/app.py .
cp ~/requirements.txt .
cp ~/.env .
chmod 600 .env

# Create systemd service file
echo "Setting up Streamlit service..."
sudo tee /etc/systemd/system/streamlit.service << EOL
[Unit]
Description=Streamlit Finance Analyzer
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/finance-analyzer
Environment="PATH=/home/ubuntu/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Start Streamlit service
echo "Starting Streamlit service..."
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit

# Install and configure Nginx
echo "Setting up Nginx..."
sudo apt-get install -y nginx

# Get EC2 instance public IP
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/streamlit << EOL
server {
    listen 80;
    server_name \$EC2_PUBLIC_IP;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable Nginx configuration
echo "Configuring Nginx..."
sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Print completion message and status
echo "Setup completed successfully!"
echo "Checking service status..."
sudo systemctl status streamlit
echo "Your application should be available at: http://$EC2_PUBLIC_IP"
echo "To check the status of the Streamlit service, run: sudo systemctl status streamlit"
echo "To view the logs, run: sudo journalctl -u streamlit -f"