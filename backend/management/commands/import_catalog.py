from django.core.management.base import BaseCommand, CommandError

from backend.services.catalog_import import import_catalog_from_yaml


class Command(BaseCommand):
    help = 'Импорт каталога товаров из YAML-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            required=True,
            help='Путь до YAML-файла (например data/shop1.yaml)',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        try:
            result = import_catalog_from_yaml(file_path)
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS('Импорт завершен успешно'))
        self.stdout.write(f"Магазин: {result['shop']}")
        self.stdout.write(f"Создано категорий: {result['categories_created']}")
        self.stdout.write(f"Создано товаров: {result['products_created']}")
        self.stdout.write(f"Создано предложений: {result['offers_created']}")
        self.stdout.write(f"Создано параметров: {result['params_created']}")
