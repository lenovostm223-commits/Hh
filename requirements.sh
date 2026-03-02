# System dependencies
apt-get update
apt-get install -y build-essential python3-dev libssl-dev p7zip-full unrar

# Uninstall all
pip uninstall aiogram aiohttp beautifulsoup4 psutil requests rarfile py7zr mega.py -y

# Reinstall properly
pip install --upgrade pip setuptools wheel
pip install aiogram==3.0.0 aiohttp==3.9.0 beautifulsoup4==4.12.0 psutil==5.9.0 requests==2.31.0 rarfile==4.0 py7zr==0.20.0
pip install --no-binary :all: mega.py
