import os
import ssl
import certifi

# Get the path to the certifi certificate
certifi_path = certifi.where()
print(f"Certifi certificate path: {certifi_path}")

# Set the environment variable
os.environ['SSL_CERT_FILE'] = certifi_path
os.environ['REQUESTS_CA_BUNDLE'] = certifi_path

# Test the certificate
try:
    context = ssl.create_default_context()
    print("SSL context created successfully.")
except Exception as e:
    print(f"Error creating SSL context: {e}")