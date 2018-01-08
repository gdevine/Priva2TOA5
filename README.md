# Priva2TOA5

Python script to download Priva-generated CSV files (containing data from Western Sydney University's Glasshouse Facility) 
from the associated gmail email address and convert those files to TOA5 format (thus enabling smart upload into HIEv) 

## Getting Started

To enable this script to log into the associated gmail address, a matching file entitled credentials.py mst be created alongside the main script file, with contents:

    gmail_login = {
        'username': "WSU.Glasshouse@gmail.com",
        'password': "<insert gmail password>"
    }

### Prerequisites

Python 3


## Authors

**Gerard Devine** - Hawkesbury Institute for the Environment 

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details