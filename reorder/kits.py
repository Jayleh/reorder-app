def convert_to_kits(final_products, component_products):
    # Instantiate list of dictionaries holding components for each final product
    component_quantity = []

    for components in component_products:
        # Instatnitae dictionary to append to compenent_quantity list
        bom = {}

        # Split by comma-space delimiter
        product_quantity = components.split(', ')

        for item in product_quantity:
            # Item is then split by space
            item = item.strip().split(" ")

            product = item[0]
            quantity = int(item[1])

            # Add product-quantity key-value pair to bom dictionary
            bom[product] = quantity

        # Append bom to component_quantity list
        component_quantity.append(bom)

    # Instantiate final dictionary list
    kit_boms = {}

    # Combine the two lists together
    for key, value in zip(final_products, component_quantity):
        kit_boms[key] = value

    # Edit final dictionary
    kit_boms = {"items": kit_boms}

    return kit_boms


def format_kits_dict(kits):
    # Instantiate final products and component products (holding dictionary)
    final_products = []
    component_products = []

    for key, value in kits.items():
        # Grab final products
        final_products.append(key)

        # Instantiate list to hold component names and their quantities
        component_quantity = []

        for product, quantity in value.items():
            component_quantity.append(f"{product} {quantity}")

        component_products.append(component_quantity)

    final_component_products = []

    for item in component_products:
        # join components and quantities by comma and space
        components = ", ".join(item)

        # append to final component products list
        final_component_products.append(components)

    # Instatiate dictionary for front end
    formatted_kits = {}

    for key, value in zip(final_products, final_component_products):
        formatted_kits[key] = value

    return formatted_kits
