from src.core.models import CustomUser, ClientModel

from django.db import transaction, connection
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class BulkOperations:
    """Handler for bulk operations at scale"""

    @staticmethod
    def bulk_create_users(user_data, batch_size=1000):
        """Bulk create users with optimized batch size"""
        users = []
        created_count = 0

        for data in user_data:
            user = CustomUser(**data)
            users.append(user)

            if len(users) >= batch_size:
                with transaction.atomic():
                    CustomUser.objects.bulk_create(users, ignore_conflicts=True)
                    created_count += len(users)
                    users = []
                    logger.info(f"Created {created_count} users...")

        if users:
            with transaction.atomic():
                CustomUser.objects.bulk_create(users, ignore_conflicts=True)
                created_count += len(users)

        return created_count

    @staticmethod
    def bulk_update_client_status(client_ids, new_status, batch_size=500):
        """Bulk update client status with connection reuse"""
        updated_count = 0

        for i in range(0, len(client_ids), batch_size):
            batch_ids = client_ids[i:i + batch_size]

            with transaction.atomic():
                updated = ClientModel.objects.filter(
                    id__in=batch_ids
                ).update(status=new_status)
                updated_count += updated

            logger.info(f"Updated {updated_count} clients...")

        return updated_count