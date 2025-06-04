def list_blob_files(container_client):
    blob_list = []
    for blob in container_client.list_blobs():
        blob_list.append(blob.name)
    return blob_list

def upload_blob(container_client, blob_name, data):
    container_client.upload_blob(blob_name, data, overwrite=True)

def download_blob(container_client, blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    return blob_client.download_blob().readall()