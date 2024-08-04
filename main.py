import os
import psutil
import subprocess
import docker
import numpy as np
from scapy.all import sniff, IP
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv
from threading import Thread
import logging

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Create a Docker client
client = docker.from_env()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable for network monitoring
network_issues_detected = False

# Bot functions
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your server bot. Type /help to get a list of commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        '/help - List of commands\n'
        '/reboot - Reboot the server\n'
        '/newvpn - Create a new VPN connection\n'
        '/status - Server status'
    )

def reboot(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Rebooting the server...')
    subprocess.run(['sudo', 'reboot'])

def new_vpn(update: Update, context: CallbackContext) -> None:
    try:
        # Stop the current VPN
        containers = client.containers.list(all=True, filters={"ancestor": "xtrime/antizapret-vpn-docker"})
        for container in containers:
            container.stop()
            container.remove()

        # Start a new VPN
        client.containers.run("xtrime/antizapret-vpn-docker", detach=True)
        update.message.reply_text('A new VPN connection has been established.')
    except Exception as e:
        update.message.reply_text(f'Error creating VPN: {e}')

def status(update: Update, context: CallbackContext) -> None:
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    status_message = (
        f"CPU Load: {cpu_usage}%\n"
        f"Memory Usage: {memory.percent}%\n"
        f"Disk Free Space: {disk.percent}%"
    )

    update.message.reply_text(status_message)

def monitor_network():
    global network_issues_detected

    def packet_callback(packet):
        if IP in packet:
            ip_layer = packet[IP]
            # Example analysis: consider suspicious if TTL is less than 10
            if ip_layer.ttl < 10:
                logger.warning(f"Suspicious packet detected: {ip_layer.src} -> {ip_layer.dst}")
                network_issues_detected = True

    # Start the sniffer in the background
    sniff(filter="ip", prn=packet_callback, store=0)

def send_alerts():
    global network_issues_detected
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    while True:
        if network_issues_detected:
            alert_message = "Network issues detected!"
            dispatcher.bot.send_message(chat_id='YOUR_CHAT_ID', text=alert_message)
            # Reset the flag after sending the notification
            network_issues_detected = False

def configure_firewall():
    try:
        # Example setup of iptables or ufw
        subprocess.run(['sudo', 'ufw', 'enable'])
        subprocess.run(['sudo', 'ufw', 'allow', '22'])  # SSH access
        subprocess.run(['sudo', 'ufw', 'allow', '1194'])  # OpenVPN port
        subprocess.run(['sudo', 'ufw', 'default', 'deny', 'incoming'])  # Deny incoming by default
        subprocess.run(['sudo', 'ufw', 'default', 'allow', 'outgoing'])  # Allow outgoing by default
    except Exception as e:
        logger.error(f'Firewall configuration error: {e}')

def configure_shadowsocks():
    try:
        # Start and configure Shadowsocks
        subprocess.run(['sudo', 'systemctl', 'enable', 'shadowsocks-libev'])
        subprocess.run(['sudo', 'systemctl', 'start', 'shadowsocks-libev'])
        logger.info("Shadowsocks is up and running.")
    except Exception as e:
        logger.error(f'Shadowsocks configuration error: {e}')

def configure_openvpn():
    try:
        # Restart OpenVPN service to apply updates
        subprocess.run(['sudo', 'systemctl', 'restart', 'openvpn'])
        logger.info("OpenVPN restarted with the new configuration.")
    except Exception as e:
        logger.error(f'OpenVPN configuration error: {e}')

def update_system():
    try:
        subprocess.run(['sudo', 'apt-get', 'update'])
        subprocess.run(['sudo', 'apt-get', 'upgrade', '-y'])
        logger.info("System updated.")
    except Exception as e:
        logger.error(f'System update error: {e}')

def setup_fail2ban():
    try:
        subprocess.run(['sudo', 'systemctl', 'enable', 'fail2ban'])
        subprocess.run(['sudo', 'systemctl', 'start', 'fail2ban'])
        logger.info("Fail2ban is set up and running.")
    except Exception as e:
        logger.error(f'Fail2ban setup error: {e}')

def main() -> None:
    configure_firewall()
    configure_shadowsocks()
    configure_openvpn()
    update_system()
    setup_fail2ban()

    # Create and start the bot
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("reboot", reboot))
    dispatcher.add_handler(CommandHandler("newvpn", new_vpn))
    dispatcher.add_handler(CommandHandler("status", status))

    # Start network monitoring in a separate thread
    monitor_thread = Thread(target=monitor_network)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Start sending alerts in a separate thread
    alert_thread = Thread(target=send_alerts)
    alert_thread.daemon = True
    alert_thread.start()

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
