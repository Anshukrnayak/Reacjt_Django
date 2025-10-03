# database_router.py
class PartitionRouter:
    """
    Database router for partitioning across multiple databases
    """
    def db_for_read(self, model, **hints):
        if hasattr(model, 'partition_key'):
            # Route based on partition key for reads
            instance = hints.get('instance')
            if instance and hasattr(instance, 'partition_key'):
                return f'partition_{instance.partition_key % 3}'  # 3 read replicas
        return 'default'

    def db_for_write(self, model, **hints):
        if hasattr(model, 'partition_key'):
            instance = hints.get('instance')
            if instance and hasattr(instance, 'partition_key'):
                return f'partition_{instance.partition_key % 2}'  # 2 write shards
        return 'default'

# settings.py - Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crm_primary',
        'USER': 'crm_user',
        'PASSWORD': 'secure_password',
        'HOST': 'primary.db.cluster.local',
        'PORT': '5432',
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    },
    'partition_0': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crm_shard_0',
        'USER': 'crm_user',
        'PASSWORD': 'secure_password',
        'HOST': 'shard0.db.cluster.local',
        'PORT': '5432',
    },
    'partition_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crm_shard_1',
        'USER': 'crm_user',
        'PASSWORD': 'secure_password',
        'HOST': 'shard1.db.cluster.local',
        'PORT': '5432',
    },
    'read_replica_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crm_replica_1',
        'USER': 'crm_user',
        'PASSWORD': 'secure_password',
        'HOST': 'replica1.db.cluster.local',
        'PORT': '5432',
    }
}

DATABASE_ROUTERS = ['myapp.database_router.PartitionRouter']