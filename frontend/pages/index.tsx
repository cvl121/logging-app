import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { logsApi } from '@/lib/api';
import { LogFilters, LogFiltering, SeverityLevel } from '@/types/log';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, subDays } from 'date-fns';

const COLORS = {
  [SeverityLevel.DEBUG]: '#9CA3AF',
  [SeverityLevel.INFO]: '#3B82F6',
  [SeverityLevel.WARNING]: '#F59E0B',
  [SeverityLevel.ERROR]: '#EF4444',
  [SeverityLevel.CRITICAL]: '#8B5CF6',
};

const DashboardPage = () => {
  const [filters, setFilters] = useState<LogFilters>({
    start_date: format(subDays(new Date(), 7), "yyyy-MM-dd'T'HH:mm"),
    end_date: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
  });
  const [severityData, setSeverityData] = useState<LogFiltering[]>([]);
  const [sourceData, setSourceData] = useState<LogFiltering[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<LogFiltering[]>([]);
  const [histogramData, setHistogramData] = useState<any[]>([]);
  const [histogramSource, setHistogramSource] = useState<string>('');
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    console.log('[Dashboard] Filters changed, fetching data:', filters);
    fetchDashboardData();
  }, [filters]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      console.log('[Dashboard] Fetching dashboard data');

      // Fetch aggregated data by severity
      const severityResponse = await logsApi.getAggregatedLogs('severity', filters);
      console.log('[Dashboard] Severity data:', severityResponse.aggregations.length, 'items');
      setSeverityData(severityResponse.aggregations);
      setTotalCount(severityResponse.total_count);

      // Fetch aggregated data by source
      const sourceResponse = await logsApi.getAggregatedLogs('source', filters);
      console.log('[Dashboard] Source data:', sourceResponse.aggregations.length, 'items');
      setSourceData(sourceResponse.aggregations.slice(0, 10)); // Top 10 sources

      // Fetch time series data
      const timeResponse = await logsApi.getAggregatedLogs('date', filters);
      console.log('[Dashboard] Time series data:', timeResponse.aggregations.length, 'items');
      setTimeSeriesData(timeResponse.aggregations);

      // Fetch sources for histogram filter
      const sourcesData = await logsApi.getSources();
      setSources(sourcesData);

      // Fetch histogram data
      await fetchHistogramData();
    } catch (err: any) {
      console.error('[Dashboard] Failed to fetch dashboard data:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch dashboard data';
      console.error('[Dashboard] Error message:', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistogramData = async () => {
    try {
      console.log('[Dashboard] Fetching histogram data');
      const histogramResponse = await logsApi.getHistogram({
        start_date: filters.start_date,
        end_date: filters.end_date,
        source: histogramSource || undefined
      });
      console.log('[Dashboard] Histogram data:', histogramResponse.histogram);
      setHistogramData(histogramResponse.histogram);
    } catch (err: any) {
      console.error('[Dashboard] Failed to fetch histogram:', err);
    }
  };

  useEffect(() => {
    if (!loading) {
      fetchHistogramData();
    }
  }, [histogramSource]);

  const handleDateChange = (key: 'start_date' | 'end_date', value: string) => {
    setFilters({ ...filters, [key]: value });
  };

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Analytics and insights for your logs
        </p>
      </div>

      {/* Simple Date Range Filter for Dashboard */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-semibold mb-4">Date Range</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="datetime-local"
              value={filters.start_date || ''}
              onChange={(e) => handleDateChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="datetime-local"
              value={filters.end_date || ''}
              onChange={(e) => handleDateChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <button
              onClick={() => setFilters({
                start_date: format(subDays(new Date(), 7), "yyyy-MM-dd'T'HH:mm"),
                end_date: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
              })}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
            >
              Reset to Last 7 Days
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Logs</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{totalCount}</p>
            </div>
            {severityData.map((item) => (
              <div key={item.severity} className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-500">{item.severity}</h3>
                <p className="text-3xl font-bold text-gray-900 mt-2">{item.count}</p>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Severity Distribution - Pie Chart */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Severity Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={severityData}
                    dataKey="count"
                    nameKey="severity"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => `${entry.severity}: ${entry.count}`}
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.severity as SeverityLevel] || '#6B7280'} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Top Sources - Bar Chart */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Top Sources</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sourceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="source" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Time Series - Line Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Log Trend Over Time</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => {
                    try {
                      return format(new Date(value), 'MMM dd');
                    } catch {
                      return value;
                    }
                  }}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => {
                    try {
                      return format(new Date(value), 'yyyy-MM-dd');
                    } catch {
                      return value;
                    }
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} name="Log Count" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Severity Distribution Histogram */}
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Severity Distribution Histogram</h2>
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">Filter by Source:</label>
                <select
                  value={histogramSource}
                  onChange={(e) => setHistogramSource(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Sources</option>
                  {sources.map((source) => (
                    <option key={source} value={source}>{source}</option>
                  ))}
                </select>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3B82F6" name="Log Count">
                  {histogramData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.severity as SeverityLevel] || '#6B7280'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-gray-600 mt-2">
              Showing severity distribution for {histogramSource || 'all sources'} within the selected date range
            </p>
          </div>

          {/* Data Table */}
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h2 className="text-xl font-semibold mb-4">Severity Breakdown</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Severity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Count
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Percentage
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {severityData.map((item) => (
                    <tr key={item.severity}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                          style={{
                            backgroundColor: COLORS[item.severity as SeverityLevel] + '20',
                            color: COLORS[item.severity as SeverityLevel],
                          }}
                        >
                          {item.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {totalCount > 0 ? ((item.count / totalCount) * 100).toFixed(2) : 0}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
};

export default DashboardPage;
