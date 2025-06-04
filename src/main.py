import yaml
from azure.storage.blob import BlobServiceClient
from blob_utils import list_blob_files, download_blob, upload_blob
from comtrade_parser import parse_cfg, parse_dat
from csv_writer import write_csv
import os

# def load_config(config_path):
#     with open(config_path, 'r') as file:
#         return yaml.safe_load(file)

def main():
    # Load configuration
    #config = load_config('../config.yaml')
    connection_string = os.getenv('AZURE_CONNECTION_STRING')
    input_container = os.getenv('AZURE_SOURCE_CONTAINER')
    output_container = os.getenv('AZURE_DESTINATION_CONTAINER')
    print(connection_string,"--->",input_container,"---->",output_container)

    # Set up blob clients
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    input_container_client = blob_service_client.get_container_client(input_container)
    output_container_client = blob_service_client.get_container_client(output_container)
    print("connected successfully to Azure Blob Storage")

    # List all blobs in the input container
    blobs = list(input_container_client.list_blobs())
    blob_names = [b.name for b in blobs]
    blob_names_lower = [b.lower() for b in blob_names]
    blob_dict = {b.name: b for b in blobs}
    cfg_blobs = [b for b in blob_names if b.lower().endswith('.cfg')]

    output_blobs = {b.name: b for b in output_container_client.list_blobs()}

    for cfg_blob in cfg_blobs:
        dat_blob = cfg_blob[:-4] + '.dat'
        output_blob = cfg_blob[:-4] + '.csv'
        # Case-insensitive check for corresponding DAT file
        if dat_blob.lower() in blob_names_lower:
            dat_blob_actual = blob_names[blob_names_lower.index(dat_blob.lower())]
            # Get last modified times
            cfg_time = blob_dict[cfg_blob].last_modified
            dat_time = blob_dict[dat_blob_actual].last_modified
            output_time = output_blobs[output_blob].last_modified if output_blob in output_blobs else None
            # Process if output doesn't exist or is older than either input
            if (output_time is None) or (output_time < cfg_time) or (output_time < dat_time):
                cfg_data = download_blob(input_container_client, cfg_blob).decode('utf-8')
                dat_data = download_blob(input_container_client, dat_blob_actual)
                metadata, channels = parse_cfg(cfg_data)
                data = parse_dat(dat_data, channels, metadata)
                csv_content = write_csv(metadata, channels, data)
                upload_blob(output_container_client, output_blob, csv_content.encode('utf-8'))
                print(f"Processed {cfg_blob} and {dat_blob} to {output_blob}")
            else:
                print(f"Skipping {cfg_blob}: output CSV is up-to-date.")
        else:
            print(f"Missing DAT file for {cfg_blob}")

if __name__ == "__main__":
    main()
