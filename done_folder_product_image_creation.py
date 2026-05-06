import os
import base64
import xmlrpc.client
import logging

_logger = logging.getLogger(__name__)

# Odoo connection details
url = 'https://circleimport.odoo.com'
db = 'yourodoopartner-circle1-main-12919881'
username = 'admin'
password = '5pC4BX_7Vg36'

# Odoo connection
odoo_connection = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
odoo_model = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Authenticate
current_user_id = odoo_connection.authenticate(db, username, password, {})

# Directory path
# path = '/home/broadtech/Desktop/test'
path = '/home/broadtech/Desktop/Done'

# Function to check if a part of the filename is valid
def is_valid_part(part):
    return len(part) > 1 and (part.isdigit() or any(char.isalpha() for char in part))

if current_user_id:
    # List of company IDs to process
    company_ids_to_process = [1, 2]

    # Process each company separately
    for company_id in company_ids_to_process:
        print(f"Processing for company ID: {company_id}")

        # Collect products by company and default_code
        unique_products = {}

        # Search products with non-empty default_code for the current company
        product_ids = odoo_model.execute_kw(db, current_user_id, password, 'product.template', 'search', [
            [('default_code', '!=', False), ('company_id', '=', company_id)]
        ])

        # Read product details
        product_data = odoo_model.execute_kw(db, current_user_id, password, 'product.template', 'read',
                                             [product_ids], {'fields': ['default_code', 'company_id']})

        for product in product_data:
            default_code = product['default_code']
            unique_key = (company_id, default_code)

            if unique_key not in unique_products:
                unique_products[unique_key] = product

        for (company_id, default_code), product in unique_products.items():
            print(f"Default Code: {default_code}, Company ID: {company_id}, Product: {product}")

            # Process the files in the folder
            if os.path.isdir(path) and os.path.exists(path):
                files = os.listdir(path)

                for filename in files:
                    name_without_extension = os.path.splitext(filename)[0]
                    parts = name_without_extension.split('_')

                    clean_part = None
                    for part in parts:
                        if is_valid_part(part):
                            clean_part = part
                            break

                    if clean_part:
                        print(f"Processing file with valid part (default code): {clean_part}")

                        # Check if the clean_part matches any product's default_code for the current company
                        if default_code == clean_part:
                            print(f"Matched product for company {company_id} with default_code {default_code}")
                            file_path = os.path.join(path, filename)
                            if os.path.isfile(file_path):
                                with open(file_path, 'rb') as file:
                                    image_data = file.read()
                                    image_base64 = base64.b64encode(image_data).decode('utf-8')

                                # img_file_obj = odoo_model.execute_kw(db, current_user_id, password, 'product.image','search', [[['name', '=', filename]]])

                                # if not img_file_obj:
                                # Create product.image record
                                image_values = {
                                    'product_tmpl_id': product['id'],
                                    'image_1920': image_base64,
                                    'name': filename,
                                }
                                odoo_model.execute_kw(db, current_user_id, password, 'product.image', 'create', [image_values])
                                print(f"Created product.image for product {product['id']} (default_code: {default_code})")





















