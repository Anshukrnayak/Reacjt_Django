from .models import LeadModel, ClientModel


class QueryOptimizer:
    """Optimized query patterns for large datasets"""

    @staticmethod
    def get_leads_by_designation(designation_name, limit=1000, offset=0):
        """Optimized lead query with proper indexing"""
        return LeadModel.objects.select_related(
            'user', 'designation'
        ).filter(
            designation__name=designation_name,
            is_archived=False,
            status='active'
        ).only(
            'user__first_name',
            'user__last_name',
            'user__email',
            'designation__name',
            'experience',
            'salary',
            'status'
        ).order_by('-created_at')[offset:offset + limit]

    @staticmethod
    def get_clients_by_lead_performance(min_score=80, limit=500):
        """Get high-performing lead clients"""
        return ClientModel.objects.select_related(
            'manage_by',
            'manage_by__user'
        ).filter(
            manage_by__performance_score__gte=min_score,
            status='active'
        ).only(
            'full_name',
            'email',
            'client_tier',
            'manage_by__performance_score',
            'lifetime_value'
        ).order_by('-lifetime_value')[:limit]