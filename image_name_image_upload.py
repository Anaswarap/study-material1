import os
import base64
import xmlrpc.client
import logging

_logger = logging.getLogger(__name__)


# url = 'http://broadtech:8063'
url = 'https://circleimport.odoo.com'
db = 'yourodoopartner-circle1-main-12919881'
username = 'admin'
password = '5pC4BX_7Vg36'


odoo_connection = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
odoo_model = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))


current_user_id = odoo_connection.authenticate(db, username, password, {})
if not current_user_id:
    raise Exception("Authentication failed.")


image_path = '/home/broadtech/Desktop/Done'
if not os.path.isdir(image_path):
    raise Exception("The specified folder does not exist.")


products = odoo_model.execute_kw(db, current_user_id, password, 'product.template', 'search_read', [[]], {'fields': ['id', 'name', 'default_code', 'product_template_image_ids']})
# print("products=========",products)

for product in products:
    default_code = product.get('default_code')
    print(f"Processing product: {product['name']} with default code: {default_code}")
    for filename in os.listdir(image_path):
        # print("filename=========",filename)
        name_without_extension = os.path.splitext(filename)[0]
        if name_without_extension == default_code:
            file_path = os.path.join(image_path, filename)
            if os.path.isfile(file_path):
                image_ids = product.get('product_template_image_ids', [])
                if image_ids:
                    existing_images = odoo_model.execute_kw(db, current_user_id, password, 'product.image', 'read',
                                                            [image_ids], {'fields': ['name']})
                else:
                    existing_images = []
                image_exists = any(image['name'] == filename for image in existing_images)
                # print("image_exists=========", image_exists)
                if image_exists:
                    with open(file_path, 'rb') as file:
                        image_data = file.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        odoo_model.execute_kw(db, current_user_id, password, 'product.template', 'write',
                                              [[product['id']], {
                                                  'image_1920': image_base64
                                              }])
                        print(f"Image uploaded for product {product['name']} with file {filename}")





