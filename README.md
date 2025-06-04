# Comtrade Conversion

This project is designed to read source and destination containers from YAML file, retrieve CFG files from an Azure Blob Storage container, convert the associated data to CSV format, and upload the resulting CSV files to another blob container. 

## Project Structure

```
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── blob_utils.py
│   ├── comtrade_parser.py
│   ├── csv_writer.py
│   └── config.yaml
├── requirements.txt
└── README.md
```
## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd comtrade_blob_converter
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

The project uses a `config.yaml` file to manage configuration settings. Ensure that this file contains the necessary details for connecting to your Azure Blob Storage, including:

- Source blob container name
- Destination blob container name
- Any other relevant parameters getting from secrets

## Usage

To run the application, execute the following command:

```
cd src
python main.py
```

This will initiate the process of reading the configuration, retrieving CFG files from the specified blob container, converting the data to CSV format, and uploading the CSV files to the destination blob container.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the Ntional Grid License. 
