from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timezone, timedelta
from app.database.mongodb import get_database
from bson import ObjectId

router = APIRouter()

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def convert_utc_to_ist(utc_datetime: datetime) -> str:
    """Convert UTC datetime to IST string"""
    if utc_datetime.tzinfo is None:
        # Assume UTC if no timezone info
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    ist_datetime = utc_datetime.astimezone(IST)
    return ist_datetime.isoformat()

class TodayOverview(BaseModel):
    scans_today: int
    alerts: int

class ScanSummary(BaseModel):
    scan_id: str
    product_name: str
    rating: str
    category: str
    concerns: int
    timestamp: str
    processing_level: str

class AlertItem(BaseModel):
    alert_id: str
    product_name: str
    alert_type: str  # "high_concerns", "poor_rating", "highly_processed", "allergen_warning"
    alert_message: str
    severity: str  # "high", "medium", "low"
    timestamp: str
    scan_id: str

class WeeklyStats(BaseModel):
    total_scans: int
    healthy_products: int  # rating "good" or "excellent"
    concerning_products: int  # rating "poor" or products with high concerns
    average_concerns_per_product: float
    most_scanned_category: str

class DashboardResponse(BaseModel):
    today_overview: TodayOverview
    recent_scans: List[ScanSummary]
    alerts: List[AlertItem]
    weekly_stats: WeeklyStats

def generate_alerts_from_scan(scan_data: Dict[str, Any], scan_id: str, timestamp: datetime) -> List[AlertItem]:
    """Generate consolidated alerts based on scan data"""
    response_data = scan_data.get("response", {})
    product_name = response_data.get("product_name", "Unknown Product")
    
    # Collect all concerns for this product
    alert_messages = []
    alert_types = []
    max_severity = "low"
    
    # Check for poor rating
    rating = response_data.get("rating", "").lower()
    if rating == "poor":
        alert_messages.append("📉 Poor nutritional rating")
        alert_types.append("poor_rating")
        max_severity = "high"
    
    # Check for high concerns
    concerns = response_data.get("concerns", 0)
    if concerns >= 3:
        alert_messages.append(f"🚨 {concerns} ingredient concerns")
        alert_types.append("high_concerns")
        if concerns >= 5:
            max_severity = "high"
        elif max_severity != "high":
            max_severity = "medium"
    
    # Check for highly processed foods
    processing_level = response_data.get("processing_level", "").lower()
    if processing_level == "highly_processed":
        alert_messages.append("🏭 Highly processed")
        alert_types.append("highly_processed")
        if max_severity == "low":
            max_severity = "medium"
    
    # Check for allergens
    allergens = response_data.get("allergens", [])
    if allergens:
        alert_messages.append(f"⚠️ Contains allergens: {', '.join(allergens)}")
        alert_types.append("allergen_warning")
        max_severity = "high"
    
    # If no alerts, return empty list
    if not alert_messages:
        return []
    
    # Create single consolidated alert
    consolidated_message = f"{product_name} - " + " | ".join(alert_messages)
    consolidated_alert_type = "_".join(alert_types)
    
    return [AlertItem(
        alert_id=f"{scan_id}_{consolidated_alert_type}",
        product_name=product_name,
        alert_type=consolidated_alert_type,
        alert_message=consolidated_message,
        severity=max_severity,
        timestamp=convert_utc_to_ist(timestamp),
        scan_id=scan_id
    )]

@router.get("/overview/{user_id}", response_model=DashboardResponse)
async def get_dashboard_overview(
    user_id: str,
    db=Depends(get_database)
):
    """Get dashboard overview for a user"""
    try:
        history_collection = db['history']
        
        # Get today's date range
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Get today's scans
        today_scans = list(history_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_of_day, "$lte": end_of_day}
        }).sort("timestamp", -1))
        
        # Get recent scans (last 10)
        recent_scans = list(history_collection.find({
            "user_id": user_id
        }).sort("timestamp", -1).limit(10))
        
        # Generate alerts from recent scans
        all_alerts = []
        for scan in recent_scans:
            scan_id = str(scan["_id"])
            timestamp = scan.get("timestamp")
            alerts = generate_alerts_from_scan(scan, scan_id, timestamp)
            all_alerts.extend(alerts)
        
        # Sort alerts by severity and timestamp
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_alerts.sort(key=lambda x: (severity_order.get(x.severity, 3), x.timestamp), reverse=True)
        
        # Limit to most recent/important alerts
        all_alerts = all_alerts[:10]
        
        # Create scan summaries
        scan_summaries = []
        for scan in recent_scans:
            response_data = scan.get("response", {})
            timestamp = scan.get("timestamp")
            scan_summaries.append(ScanSummary(
                scan_id=str(scan["_id"]),
                product_name=response_data.get("product_name", "Unknown Product"),
                rating=response_data.get("rating", "unknown"),
                category=response_data.get("category", "unknown"),
                concerns=response_data.get("concerns", 0),
                timestamp=convert_utc_to_ist(timestamp) if timestamp else "",
                processing_level=response_data.get("processing_level", "unknown")
            ))
        
        # Calculate weekly stats (last 7 days)
        week_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7)
        
        weekly_scans = list(history_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": week_ago}
        }))
        
        healthy_count = 0
        concerning_count = 0
        total_concerns = 0
        category_counts = {}
        
        for scan in weekly_scans:
            response_data = scan.get("response", {})
            rating = response_data.get("rating", "").lower()
            concerns = response_data.get("concerns", 0)
            category = response_data.get("category", "unknown")
            
            if rating in ["good", "excellent"]:
                healthy_count += 1
            elif rating == "poor" or concerns >= 3:
                concerning_count += 1
            
            total_concerns += concerns
            category_counts[category] = category_counts.get(category, 0) + 1
        
        most_scanned_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "none"
        avg_concerns = total_concerns / len(weekly_scans) if weekly_scans else 0
        
        weekly_stats = WeeklyStats(
            total_scans=len(weekly_scans),
            healthy_products=healthy_count,
            concerning_products=concerning_count,
            average_concerns_per_product=round(avg_concerns, 2),
            most_scanned_category=most_scanned_category
        )
        
        return DashboardResponse(
            today_overview=TodayOverview(
                scans_today=len(today_scans),
                alerts=len(all_alerts)
            ),
            recent_scans=scan_summaries,
            alerts=all_alerts,
            weekly_stats=weekly_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans/today/{user_id}")
async def get_today_scans(
    user_id: str,
    db=Depends(get_database)
):
    """Get today's scans for a user"""
    try:
        history_collection = db['history']
        
        # Get today's date range
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        today_scans = list(history_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_of_day, "$lte": end_of_day}
        }).sort("timestamp", -1))
        
        scan_summaries = []
        for scan in today_scans:
            response_data = scan.get("response", {})
            timestamp = scan.get("timestamp")
            scan_summaries.append(ScanSummary(
                scan_id=str(scan["_id"]),
                product_name=response_data.get("product_name", "Unknown Product"),
                rating=response_data.get("rating", "unknown"),
                category=response_data.get("category", "unknown"),
                concerns=response_data.get("concerns", 0),
                timestamp=convert_utc_to_ist(timestamp) if timestamp else "",
                processing_level=response_data.get("processing_level", "unknown")
            ))
        
        return {
            "count": len(scan_summaries),
            "scans": scan_summaries
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{user_id}")
async def get_user_alerts(
    user_id: str,
    limit: int = 20,
    db=Depends(get_database)
):
    """Get alerts for a user based on their scan history"""
    try:
        history_collection = db['history']
        
        # Get recent scans (last 30 days)
        thirty_days_ago = datetime.now().replace(day=datetime.now().day - 30)
        recent_scans = list(history_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": thirty_days_ago}
        }).sort("timestamp", -1))
        
        # Generate alerts
        all_alerts = []
        for scan in recent_scans:
            scan_id = str(scan["_id"])
            timestamp = scan.get("timestamp")
            alerts = generate_alerts_from_scan(scan, scan_id, timestamp)
            all_alerts.extend(alerts)
        
        # Sort and limit alerts
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_alerts.sort(key=lambda x: (severity_order.get(x.severity, 3), x.timestamp), reverse=True)
        all_alerts = all_alerts[:limit]
        
        return {
            "count": len(all_alerts),
            "alerts": all_alerts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
