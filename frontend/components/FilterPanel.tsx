import React, { useState, useEffect } from 'react';
import { SeverityLevel, LogFilters } from '@/types/log';
import { logsApi } from '@/lib/api';

interface FilterPanelProps {
  filters: LogFilters;
  onFilterChange: (filters: LogFilters) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ filters, onFilterChange }) => {
  const [searchValue, setSearchValue] = useState(filters.search || '');
  const [sources, setSources] = useState<string[]>([]);
  const [sourceSearchValue, setSourceSearchValue] = useState(filters.source || '');
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);

  // Fetch available sources
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const sourcesData = await logsApi.getSources();
        setSources(sourcesData);
      } catch (err) {
        console.error('Failed to fetch sources:', err);
      }
    };
    fetchSources();
  }, []);

  // Debounce search input
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchValue !== filters.search) {
        onFilterChange({ ...filters, search: searchValue || undefined, page: 1 });
      }
    }, 500); // Wait 500ms after user stops typing

    return () => clearTimeout(timeoutId);
  }, [searchValue]);

  // Update local state when filters change externally
  useEffect(() => {
    setSearchValue(filters.search || '');
  }, [filters.search]);

  useEffect(() => {
    setSourceSearchValue(filters.source || '');
  }, [filters.source]);

  const handleInputChange = (key: keyof LogFilters, value: string) => {
    onFilterChange({ ...filters, [key]: value || undefined, page: 1 });
  };

  const handleSourceSelect = (source: string) => {
    setSourceSearchValue(source);
    onFilterChange({ ...filters, source: source || undefined, page: 1 });
    setShowSourceDropdown(false);
  };

  const filteredSources = sources.filter(source =>
    source.toLowerCase().includes(sourceSearchValue.toLowerCase())
  );

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h2 className="text-xl font-semibold mb-4">Filters</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search Message
          </label>
          <input
            type="text"
            placeholder="Search in messages..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Severity
          </label>
          <select
            value={filters.severity || ''}
            onChange={(e) => handleInputChange('severity', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            {Object.values(SeverityLevel).map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Source
          </label>
          <input
            type="text"
            placeholder="Search or select source..."
            value={sourceSearchValue}
            onChange={(e) => setSourceSearchValue(e.target.value)}
            onFocus={() => setShowSourceDropdown(true)}
            onBlur={() => setTimeout(() => setShowSourceDropdown(false), 200)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {showSourceDropdown && filteredSources.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
              {filteredSources.map((source) => (
                <div
                  key={source}
                  onClick={() => handleSourceSelect(source)}
                  className="px-3 py-2 hover:bg-blue-50 cursor-pointer text-sm"
                >
                  {source}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="datetime-local"
            value={filters.start_date || ''}
            onChange={(e) => handleInputChange('start_date', e.target.value)}
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
            onChange={(e) => handleInputChange('end_date', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <select
            value={filters.sort_by || 'timestamp'}
            onChange={(e) => handleInputChange('sort_by', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="timestamp">Timestamp</option>
            <option value="severity">Severity</option>
            <option value="source">Source</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sort Order
          </label>
          <select
            value={filters.sort_order || 'desc'}
            onChange={(e) => handleInputChange('sort_order', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={() => {
              setSearchValue('');
              setSourceSearchValue('');
              onFilterChange({ page: 1, page_size: 50, sort_by: 'timestamp', sort_order: 'desc' });
            }}
            className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;
