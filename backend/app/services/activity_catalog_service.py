"""
Activity Catalog Service

Manages the activity catalog and provides activity information
"""

import sqlite3
from typing import List, Dict, Optional


class ActivityCatalogService:
    """Service for managing activity catalog"""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def get_all_activities(self, active_only: bool = True) -> List[Dict]:
        """Get all activities"""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM activity_catalog'
        if active_only:
            query += ' WHERE active = 1'
        query += ' ORDER BY category, name'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_activities_by_category(self, category: str) -> List[Dict]:
        """Get activities in a specific category"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM activity_catalog
            WHERE category = ? AND active = 1
            ORDER BY name
        ''', (category,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_activity_by_id(self, activity_id: str) -> Optional[Dict]:
        """Get activity by ID"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM activity_catalog
            WHERE id = ?
        ''', (activity_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with activity counts"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as activity_count
            FROM activity_catalog
            WHERE active = 1
            GROUP BY category
            ORDER BY category
        ''')
        
        rows = cursor.fetchall()
        
        # Add metadata for each category
        category_info = {
            'wellbeing': {'name': 'Well-being', 'icon': '🧘', 'description': 'Activities for mental wellness'},
            'popular': {'name': 'Most Popular', 'icon': '⭐', 'description': 'Popular physical activities'},
            'exercise': {'name': 'Exercise', 'icon': '🏃', 'description': 'Fitness and workout activities'}
        }
        
        result = []
        for row in rows:
            category = row['category']
            info = category_info.get(category, {'name': category.title(), 'icon': '📋'})
            result.append({
                'id': category,
                'name': info['name'],
                'icon': info['icon'],
                'description': info.get('description', ''),
                'activity_count': row['activity_count']
            })
        
        return result
    
    def search_activities(self, query: str) -> List[Dict]:
        """Search activities by name or description"""
        cursor = self.conn.cursor()
        
        search_term = f'%{query}%'
        cursor.execute('''
            SELECT * FROM activity_catalog
            WHERE active = 1
            AND (name LIKE ? OR description LIKE ? OR id LIKE ?)
            ORDER BY name
        ''', (search_term, search_term, search_term))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def add_activity(self, activity_data: Dict) -> str:
        """Add a new activity to catalog"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_catalog 
            (id, name, category, icon, default_duration, requires_duration, description, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            activity_data['id'],
            activity_data['name'],
            activity_data['category'],
            activity_data.get('icon', '📋'),
            activity_data.get('default_duration', 30),
            activity_data.get('requires_duration', 1),
            activity_data.get('description', ''),
            activity_data.get('active', 1)
        ))
        
        self.conn.commit()
        return activity_data['id']
    
    def update_activity(self, activity_id: str, updates: Dict) -> bool:
        """Update an activity"""
        cursor = self.conn.cursor()
        
        # Build update query dynamically
        allowed_fields = ['name', 'category', 'icon', 'default_duration', 
                         'requires_duration', 'description', 'active']
        
        update_fields = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f'{field} = ?')
                values.append(value)
        
        if not update_fields:
            return False
        
        values.append(activity_id)
        
        query = f"UPDATE activity_catalog SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def deactivate_activity(self, activity_id: str) -> bool:
        """Deactivate an activity (soft delete)"""
        return self.update_activity(activity_id, {'active': 0})
    
    def get_activity_stats(self, user_id: int) -> Dict:
        """Get user's activity statistics"""
        cursor = self.conn.cursor()
        
        # Total completions per activity
        cursor.execute('''
            SELECT 
                ac.activity_id,
                cat.name,
                cat.icon,
                cat.category,
                COUNT(*) as completion_count,
                SUM(ac.duration_minutes) as total_minutes
            FROM activity_completions ac
            JOIN activity_catalog cat ON ac.activity_id = cat.id
            WHERE ac.user_id = ?
            GROUP BY ac.activity_id
            ORDER BY completion_count DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        
        return {
            'activities': [dict(row) for row in rows],
            'total_activities': len(rows),
            'total_completions': sum(row['completion_count'] for row in rows),
            'total_minutes': sum(row['total_minutes'] or 0 for row in rows)
        }
