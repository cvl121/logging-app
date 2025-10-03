export enum SeverityLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARNING = "WARNING",
  ERROR = "ERROR",
  CRITICAL = "CRITICAL",
}

export interface Log {
  id: number;
  timestamp: string;
  message: string;
  severity: SeverityLevel;
  source: string;
}

export interface LogCreate {
  message: string;
  severity: SeverityLevel;
  source: string;
  timestamp?: string;
}

export interface LogUpdate {
  message?: string;
  severity?: SeverityLevel;
  source?: string;
  timestamp?: string;
}

export interface LogListResponse {
  items: Log[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LogFiltering {
  severity?: string;
  source?: string;
  count: number;
  date?: string;
}

export interface LogFilteringResponse {
  aggregations: LogFiltering[];
  total_count: number;
}

export interface LogFilters {
  page?: number;
  page_size?: number;
  severity?: SeverityLevel | string;
  source?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
