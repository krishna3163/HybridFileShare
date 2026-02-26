from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
import socket
import uuid
import time
import logging

# Set logging level for discovery
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Discovery")

class MultitrackListener:
    def __init__(self):
        self.discovered_devices = {}

    def remove_service(self, zeroconf, type, name):
        if name in self.discovered_devices:
            dev = self.discovered_devices.pop(name)
            logger.info(f"👋 Device lost: {dev['name']}")

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            addresses = ["%s" % (socket.inet_ntoa(addr)) for addr in info.addresses]
            properties = {k.decode(): v.decode() if isinstance(v, bytes) else v 
                          for k, v in info.properties.items()}
            
            device_info = {
                "name": name.split('.')[0],
                "ip": addresses[0] if addresses else "unknown",
                "port": info.port,
                "deviceId": properties.get('deviceId', 'unknown'),
                "platform": properties.get('platform', 'unknown'),
                "version": properties.get('version', 'unknown')
            }
            self.discovered_devices[name] = device_info
            logger.info(f"✨ Device found: {device_info['name']} at {device_info['ip']}:{device_info['port']} [{device_info['platform']}]")

    def update_service(self, zeroconf, type, name):
        pass

class MultitrackDiscovery:
    def __init__(self, device_name=None, port=9001):
        self.zeroconf = Zeroconf()
        self.device_id = str(uuid.uuid4())[:8]
        self.device_name = device_name or f"HybridLink-PC-{socket.gethostname()}"
        self.port = port
        self.service_type = "_hybridfileshare._tcp.local."
        self.browser = None
        
    def start_advertising(self):
        desc = {
            'deviceId': self.device_id,
            'platform': 'win32',
            'deviceName': self.device_name,
            'version': '1.0.0'
        }
        
        info = ServiceInfo(
            self.service_type,
            f"{self.device_name}.{self.service_type}",
            addresses=[socket.inet_aton(self.get_ip())],
            port=self.port,
            properties=desc,
            server=f"{socket.gethostname()}.local.",
        )
        
        logger.info(f"📡 Advertising Multitrack service: {self.device_name} on {self.get_ip()}:{self.port}")
        self.zeroconf.register_service(info)
        return info

    def start_scanning(self):
        listener = MultitrackListener()
        self.browser = ServiceBrowser(self.zeroconf, self.service_type, listener)
        logger.info("🔍 Scanning for nearby multitrack devices...")
        return listener

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def stop(self):
        self.zeroconf.unregister_all_services()
        self.zeroconf.close()

if __name__ == "__main__":
    discovery = MultitrackDiscovery()
    discovery.start_advertising()
    listener = discovery.start_scanning()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        discovery.stop()
