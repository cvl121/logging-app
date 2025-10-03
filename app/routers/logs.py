from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Optional
from datetime import datetime, date
from app.database import get_db
from app.models.log import Log, SeverityLevel
from app.schemas.log import (
    LogCreate, LogUpdate, LogResponse, LogListResponse,
    LogFilteringResponse, LogFiltering
)
import math
import logging
import csv
import io

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/logs", tags=["logs"])

@router.post("", response_model=LogResponse, status_code=201)
def create_log(log: LogCreate, db: Session = Depends(get_db)):
    """Create a new log entry"""
    try:
        logger.info(f"Creating new log entry: source={log.source}, severity={log.severity}")

        # Validation
        if not log.message or len(log.message.strip()) < 3:
            logger.warning("Validation failed: Message too short")
            raise HTTPException(status_code=400, detail="Message must be at least 3 characters")

        if len(log.message) > 5000:
            logger.warning("Validation failed: Message too long")
            raise HTTPException(status_code=400, detail="Message must not exceed 5000 characters")

        if not log.source or len(log.source.strip()) < 2:
            logger.warning("Validation failed: Source too short")
            raise HTTPException(status_code=400, detail="Source must be at least 2 characters")

        if len(log.source) > 255:
            logger.warning("Validation failed: Source too long")
            raise HTTPException(status_code=400, detail="Source must not exceed 255 characters")

        if log.timestamp and log.timestamp > datetime.utcnow():
            logger.warning("Validation failed: Timestamp in future")
            raise HTTPException(status_code=400, detail="Timestamp cannot be in the future")

        db_log = Log(
            message=log.message,
            severity=log.severity,
            source=log.source,
            timestamp=log.timestamp if log.timestamp else datetime.utcnow()
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        logger.info(f"Log created successfully with ID: {db_log.id}")
        return db_log
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("", response_model=LogListResponse)
def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    search: Optional[str] = Query(None, description="Search in message field"),
    sort_by: str = Query("timestamp", description="Field to sort by (timestamp, severity, source)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db)
):
    """Get paginated list of logs with optional filters, search, and sorting"""
    try:
        logger.info(f"Fetching logs: page={page}, page_size={page_size}, severity={severity}, source={source}")
        query = db.query(Log)

        # Apply filters
        filters = []
        if severity:
            filters.append(Log.severity == severity)
        if source:
            filters.append(Log.source == source)
        if start_date:
            filters.append(Log.timestamp >= start_date)
        if end_date:
            filters.append(Log.timestamp <= end_date)
        if search:
            filters.append(Log.message.ilike(f"%{search}%"))

        if filters:
            query = query.filter(and_(*filters))

        # Apply sorting
        sort_field = getattr(Log, sort_by, Log.timestamp)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

        # Get total count
        total = query.count()
        logger.info(f"Found {total} logs matching criteria")

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        total_pages = math.ceil(total / page_size)

        return LogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Failed to fetch logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")

@router.get("/search", response_model=LogFilteringResponse)
def search_logs(
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    group_by: str = Query("severity", description="Group by field (severity, source, date, hour)"),
    db: Session = Depends(get_db)
):
    """Get aggregated log data grouped by severity, source, or time"""
    try:
        logger.info(f"Searching logs: group_by={group_by}, severity={severity}, source={source}")
        query = db.query(Log)

        # Apply filters
        filters = []
        if severity:
            filters.append(Log.severity == severity)
        if source:
            filters.append(Log.source == source)
        if start_date:
            filters.append(Log.timestamp >= start_date)
        if end_date:
            filters.append(Log.timestamp <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Aggregate based on group_by parameter
        aggregations = []

        if group_by == "severity":
            results = db.query(
                Log.severity,
                func.count(Log.id).label('count')
            ).filter(and_(*filters) if filters else True).group_by(Log.severity).all()

            aggregations = [
                LogFiltering(severity=r[0].value if hasattr(r[0], 'value') else str(r[0]), count=r[1])
                for r in results
            ]

        elif group_by == "source":
            results = db.query(
                Log.source,
                func.count(Log.id).label('count')
            ).filter(and_(*filters) if filters else True).group_by(Log.source).all()

            aggregations = [
                LogFiltering(source=r[0], count=r[1])
                for r in results
            ]

        elif group_by == "date":
            results = db.query(
                func.date(Log.timestamp).label('date'),
                func.count(Log.id).label('count')
            ).filter(and_(*filters) if filters else True).group_by(func.date(Log.timestamp)).order_by(func.date(Log.timestamp)).all()

            aggregations = [
                LogFiltering(date=str(r[0]), count=r[1])
                for r in results
            ]

        elif group_by == "hour":
            # Use strftime for SQLite compatibility
            results = db.query(
                func.strftime('%Y-%m-%d %H:00:00', Log.timestamp).label('hour'),
                func.count(Log.id).label('count')
            ).filter(and_(*filters) if filters else True).group_by(func.strftime('%Y-%m-%d %H:00:00', Log.timestamp)).order_by(func.strftime('%Y-%m-%d %H:00:00', Log.timestamp)).all()

            aggregations = [
                LogFiltering(date=str(r[0]), count=r[1])
                for r in results
            ]

        total_count = query.count()
        logger.info(f"Search returned {len(aggregations)} aggregations, total count: {total_count}")

        return LogFilteringResponse(
            aggregations=aggregations,
            total_count=total_count
        )
    except Exception as e:
        logger.error(f"Failed to search logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search logs: {str(e)}")

@router.get("/export/csv")
def export_logs_csv(
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    search: Optional[str] = Query(None, description="Search in message field"),
    db: Session = Depends(get_db)
):
    """Export logs as CSV file"""
    try:
        logger.info(f"Exporting logs to CSV: severity={severity}, source={source}")
        query = db.query(Log)

        # Apply filters
        filters = []
        if severity:
            filters.append(Log.severity == severity)
        if source:
            filters.append(Log.source == source)
        if start_date:
            filters.append(Log.timestamp >= start_date)
        if end_date:
            filters.append(Log.timestamp <= end_date)
        if search:
            filters.append(Log.message.ilike(f"%{search}%"))

        if filters:
            query = query.filter(and_(*filters))

        # Order by timestamp descending
        query = query.order_by(desc(Log.timestamp))
        logs = query.all()

        logger.info(f"Exporting {len(logs)} logs to CSV")

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['ID', 'Timestamp', 'Severity', 'Source', 'Message'])

        # Write data
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.isoformat(),
                log.severity.value if hasattr(log.severity, 'value') else str(log.severity),
                log.source,
                log.message
            ])

        # Prepare response
        output.seek(0)
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=logs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

        logger.info("CSV export completed successfully")
        return response
    except Exception as e:
        logger.error(f"Failed to export CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")

@router.get("/histogram")
def get_severity_histogram(
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: Session = Depends(get_db)
):
    """Get histogram data of log severity distribution for the selected date range and source"""
    try:
        logger.info(f"Generating severity histogram: start_date={start_date}, end_date={end_date}, source={source}")

        # Apply filters
        filters = []
        if start_date:
            filters.append(Log.timestamp >= start_date)
        if end_date:
            filters.append(Log.timestamp <= end_date)
        if source:
            filters.append(Log.source == source)

        # Get severity distribution
        query = db.query(
            Log.severity,
            func.count(Log.id).label('count')
        )

        if filters:
            query = query.filter(and_(*filters))

        results = query.group_by(Log.severity).all()

        histogram_data = [
            {
                "severity": r[0].value if hasattr(r[0], 'value') else str(r[0]),
                "count": r[1]
            }
            for r in results
        ]

        # Ensure all severity levels are present, even if count is 0
        all_severities = {s.value: 0 for s in SeverityLevel}
        for item in histogram_data:
            all_severities[item['severity']] = item['count']

        histogram_data = [
            {"severity": severity, "count": count}
            for severity, count in all_severities.items()
        ]

        logger.info(f"Histogram generated with {len(histogram_data)} severity levels")

        return {
            "histogram": histogram_data,
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "source": source
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate histogram: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate histogram: {str(e)}")

@router.get("/{log_id}", response_model=LogResponse)
def get_log(log_id: int, db: Session = Depends(get_db)):
    """Get a specific log by ID"""
    try:
        logger.info(f"Fetching log with ID: {log_id}")
        log = db.query(Log).filter(Log.id == log_id).first()
        if not log:
            logger.warning(f"Log not found: {log_id}")
            raise HTTPException(status_code=404, detail="Log not found")
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch log {log_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch log: {str(e)}")

@router.put("/{log_id}", response_model=LogResponse)
def update_log(log_id: int, log_update: LogUpdate, db: Session = Depends(get_db)):
    """Update a specific log"""
    try:
        logger.info(f"Updating log with ID: {log_id}")
        db_log = db.query(Log).filter(Log.id == log_id).first()
        if not db_log:
            logger.warning(f"Log not found for update: {log_id}")
            raise HTTPException(status_code=404, detail="Log not found")

        update_data = log_update.model_dump(exclude_unset=True)

        # Validate update data
        if 'message' in update_data:
            if len(update_data['message'].strip()) < 3:
                logger.warning("Validation failed: Message too short")
                raise HTTPException(status_code=400, detail="Message must be at least 3 characters")
            if len(update_data['message']) > 5000:
                logger.warning("Validation failed: Message too long")
                raise HTTPException(status_code=400, detail="Message must not exceed 5000 characters")

        if 'source' in update_data:
            if len(update_data['source'].strip()) < 2:
                logger.warning("Validation failed: Source too short")
                raise HTTPException(status_code=400, detail="Source must be at least 2 characters")
            if len(update_data['source']) > 255:
                logger.warning("Validation failed: Source too long")
                raise HTTPException(status_code=400, detail="Source must not exceed 255 characters")

        for field, value in update_data.items():
            setattr(db_log, field, value)

        db.commit()
        db.refresh(db_log)
        logger.info(f"Log {log_id} updated successfully")
        return db_log
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update log {log_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update log: {str(e)}")

@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    """Delete a specific log"""
    try:
        logger.info(f"Deleting log with ID: {log_id}")
        db_log = db.query(Log).filter(Log.id == log_id).first()
        if not db_log:
            logger.warning(f"Log not found for deletion: {log_id}")
            raise HTTPException(status_code=404, detail="Log not found")

        db.delete(db_log)
        db.commit()
        logger.info(f"Log {log_id} deleted successfully")
        return {"message": f"Log {log_id} deleted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete log {log_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
