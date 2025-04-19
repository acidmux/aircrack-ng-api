FROM kalilinux/kali-linux-arm64:latest

# Install dependencies
RUN apt update && apt install -y \
    python3-flask \
    wireless-tools \
    iw \
    hostapd \
    dnsmasq \
    && apt clean

# Clone shinai-fi
RUN git clone https://github.com/sensepost/shinai-fi /app
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["python3", "app.py"]