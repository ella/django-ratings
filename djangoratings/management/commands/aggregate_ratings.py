from django.core.management.base import NoArgsCommand
from django.db import transaction

# Logging must be inicialized
from djangoratings.aggregation import transfer_data

class Command(NoArgsCommand):
    help = 'Aggregate ratings'

    @transaction.commit_on_success
    def handle(self, **options):
        transfer_data()
