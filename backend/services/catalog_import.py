from pathlib import Path

import yaml
from django.db import transaction

from backend.models import Category, Parameter, Product, ProductInfo, ProductParameter, Shop


def _validate_catalog(payload: dict) -> None:
    required_keys = {'shop', 'categories', 'goods'}
    missing = required_keys.difference(payload.keys())
    if missing:
        missing_text = ', '.join(sorted(missing))
        raise ValueError(f'В YAML не хватает полей: {missing_text}')


@transaction.atomic
def import_catalog_from_yaml(file_path: str) -> dict:
    """
    Импортирует каталог товаров из yaml-файла в базу данных.
    """
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f'Файл не найден: {source}')

    with source.open('r', encoding='utf-8') as stream:
        payload = yaml.safe_load(stream) or {}

    _validate_catalog(payload)

    shop_name = str(payload['shop']).strip()
    if not shop_name:
        raise ValueError('Поле shop не должно быть пустым')

    shop, _ = Shop.objects.get_or_create(name=shop_name)

    categories_by_external_id = {}
    created_categories = 0
    for category_data in payload.get('categories', []):
        external_id = category_data.get('id')
        category_name = str(category_data.get('name', '')).strip()
        if not category_name:
            continue

        category, was_created = Category.objects.get_or_create(name=category_name)
        if was_created:
            created_categories += 1
        category.shops.add(shop)
        categories_by_external_id[external_id] = category

    ProductInfo.objects.filter(shop=shop).delete()

    created_products = 0
    created_offers = 0
    created_params = 0

    for good_data in payload.get('goods', []):
        category = categories_by_external_id.get(good_data.get('category'))
        if category is None:
            continue

        product_name = str(good_data.get('name', '')).strip()
        if not product_name:
            continue

        product, was_created = Product.objects.get_or_create(name=product_name, category=category)
        if was_created:
            created_products += 1

        offer = ProductInfo.objects.create(
            product=product,
            shop=shop,
            name=str(good_data.get('model', product_name)),
            quantity=int(good_data.get('quantity', 0)),
            price=int(good_data.get('price', 0)),
            price_rrc=int(good_data.get('price_rrc', 0)),
        )
        created_offers += 1

        for parameter_name, parameter_value in (good_data.get('parameters') or {}).items():
            parameter, _ = Parameter.objects.get_or_create(name=str(parameter_name))
            ProductParameter.objects.create(
                product_info=offer,
                parameter=parameter,
                value=str(parameter_value),
            )
            created_params += 1

    return {
        'shop': shop.name,
        'categories_created': created_categories,
        'products_created': created_products,
        'offers_created': created_offers,
        'params_created': created_params,
    }
