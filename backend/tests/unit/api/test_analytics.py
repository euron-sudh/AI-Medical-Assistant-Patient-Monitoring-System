"""Tests for the analytics API endpoints."""

import uuid
from unittest.mock import patch

def test_get_patient_overview(client, auth_headers):
    """Test getting patient overview analytics."""
    patient_id = uuid.uuid4()
    
    with patch('app.api.v1.analytics.analytics_service.get_patient_overview') as mock_service:
        mock_service.return_value = {
            "vitals_trends": [],
            "medication_adherence_pct": 100.0,
            "appointment_attendance_pct": 100.0,
            "symptom_frequency_30d": 0,
            "active_alerts_count": 0
        }
        
        response = client.get(
            f"/api/v1/analytics/patient/{patient_id}/overview",
            headers=auth_headers["patient"]
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "vitals_trends" in data
        assert data["medication_adherence_pct"] == 100.0


def test_get_doctor_overview(client, auth_headers):
    """Test getting doctor metrics overview."""
    doctor_id = uuid.uuid4()
    
    with patch('app.api.v1.analytics.analytics_service.get_doctor_overview') as mock_service:
        mock_service.return_value = {
            "total_patients": 10,
            "consultations_this_month": 5,
            "avg_consultation_duration_minutes": 15.0,
            "ai_assisted_diagnosis_count": 2
        }
        
        response = client.get(
            f"/api/v1/analytics/doctor/{doctor_id}/overview",
            headers=auth_headers["doctor"]
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_patients"] == 10
        assert data["consultations_this_month"] == 5


def test_get_system_overview(client, auth_headers):
    """Test getting system overview (admin only)."""
    with patch('app.api.v1.analytics.analytics_service.get_system_overview') as mock_service:
        mock_service.return_value = {
            "users_by_role": {"patient": 100, "doctor": 10, "admin": 2},
            "total_api_calls_today": 5000,
            "active_monitoring_alerts": 5,
            "system_uptime_pct": 99.99,
            "ai_token_usage_today": 150000
        }
        
        # Test admin access
        response = client.get(
            "/api/v1/analytics/system/overview",
            headers=auth_headers["admin"]
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["system_uptime_pct"] == 99.99
        
        # Test doctor access denied
        response = client.get(
            "/api/v1/analytics/system/overview",
            headers=auth_headers["doctor"]
        )
        assert response.status_code == 403


def test_get_ai_usage(client, auth_headers):
    """Test getting AI usage stats (admin only)."""
    with patch('app.api.v1.analytics.analytics_service.get_ai_usage') as mock_service:
        mock_service.return_value = {
            "agent_runs_by_type": {
                "symptom_analyst": 100,
                "report_reader": 50,
                "telemedicine_summarizer": 25
            },
            "total_runs": 175,
            "total_tokens_consumed": 262500,
            "estimated_cost_usd": 0.525,
            "avg_response_time_ms": 1250
        }
        
        # Test admin access
        response = client.get(
            "/api/v1/analytics/ai/usage",
            headers=auth_headers["admin"]
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_runs"] == 175
        assert data["total_tokens_consumed"] == 262500
        
        # Test patient access denied
        response = client.get(
            "/api/v1/analytics/ai/usage",
            headers=auth_headers["patient"]
        )
        assert response.status_code == 403