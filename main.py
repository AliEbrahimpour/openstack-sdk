from fastapi import FastAPI
from openstack import connection
import time
import os
import uvicorn
from dotenv import load_dotenv
from pydantic import BaseModel
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# Extract OpenStack credentials from environment variables
credentials = {
    'auth_url': os.getenv('OS_AUTH_URL'),
    'username': os.getenv('OS_USERNAME'),
    'password': os.getenv('OS_PASSWORD'),
    'project_name': os.getenv('OS_PROJECT_NAME'),
    'user_domain_name': os.getenv('OS_USER_DOMAIN_NAME'),
    'project_domain_name': os.getenv('OS_PROJECT_DOMAIN_NAME'),
    'region_name': os.getenv('OS_REGION_NAME'),
    'identity_api_version': os.getenv('OS_IDENTITY_API_VERSION'),
    'auth_version': os.getenv('OS_AUTH_VERSION'),
    'interface': 'internal'  # Specify the interface you want to use
}

# Create a connection to the OpenStack environment
conn = connection.Connection(
    **credentials,
    connect_timeout=10,  # Set your desired connect timeout in seconds
    read_timeout=60,      # Set your desired read timeout in seconds
    dentity_interface='internal',
    )

class InstanceRequest(BaseModel):
    instance_name: str

@app.post("/deploy-instance")
async def deploy_instance(request_data: InstanceRequest):
    if conn is None:
        return {"message": "Failed to establish OpenStack connection"}
    
    instance_name = request_data.instance_name
    print(instance_name)

    try:
        print(1)
        # Create an instance
        server = conn.compute.create_server(
            name=instance_name,
            flavor_id=os.getenv('OS_FLAVOR_ID'),  # Specify the flavor ID
            image_id=os.getenv('OS_IMAGE_ID'),    # Specify the image ID
            networks=[{"uuid": os.getenv('OS_NETWORK_ID')}]
        )
        print(2)
        
        # Wait for the instance to become active
        conn.compute.wait_for_server(server, status='ACTIVE', wait=600, interval=5)
        print(3)
        
        # Run a command on the instance (example: create a file)
        command = 'touch /tmp/example_file'
        conn.compute.create_server_action(server, 'os-execute', {'script': command})
        print(4)
        
        # # Wait for a short period to allow the command to complete
        # time.sleep(5)
        
        # # Create a snapshot of the instance
        # snapshot_name = f'{instance_name}_snapshot'
        # snapshot = conn.compute.create_image_server(server, name=snapshot_name)
        
        return {"message": f"Instance deployed"}
    
    except Exception as e:
        return {"message": f"An error occurred: {e}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1234)
