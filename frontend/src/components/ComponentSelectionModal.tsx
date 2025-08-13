import React, { useState, useEffect } from 'react';
import { useAppStore } from '../appStore';

interface ComponentOption {
  part_number: string;
  name: string;
  power?: number;
  price?: number;
  manufacturer?: string;
  efficiency?: number;
  suitability_score?: number;
  availability?: boolean;
  category?: string;
}

interface ComponentSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  componentType: string;
  placeholderCount: number;
  options: ComponentOption[];
  onSelect: (option: ComponentOption) => void;
  onUploadMore: () => void;
}

interface FilterOptions {
  sortBy: 'score' | 'price' | 'power' | 'efficiency';
  manufacturer: string;
  minPower: number;
  maxPower: number;
  minPrice: number;
  maxPrice: number;
}

export const ComponentSelectionModal: React.FC<ComponentSelectionModalProps> = ({
  isOpen,
  onClose,
  sessionId,
  componentType,
  placeholderCount,
  options,
  onSelect,
  onUploadMore
}) => {
  const [selectedOption, setSelectedOption] = useState<ComponentOption | null>(null);
  const [filteredOptions, setFilteredOptions] = useState<ComponentOption[]>(options);
  const [filters, setFilters] = useState<FilterOptions>({
    sortBy: 'score',
    manufacturer: '',
    minPower: 0,
    maxPower: 0,
    minPrice: 0,
    maxPrice: 0
  });
  const [loading, setLoading] = useState(false);
  const { addStatusMessage } = useAppStore();

  // Update filtered options when props or filters change
  useEffect(() => {
    let filtered = [...options];

    // Apply manufacturer filter
    if (filters.manufacturer) {
      filtered = filtered.filter(option => 
        option.manufacturer?.toLowerCase().includes(filters.manufacturer.toLowerCase())
      );
    }

    // Apply power range filter
    if (filters.minPower > 0) {
      filtered = filtered.filter(option => (option.power || 0) >= filters.minPower);
    }
    if (filters.maxPower > 0) {
      filtered = filtered.filter(option => (option.power || 0) <= filters.maxPower);
    }

    // Apply price range filter  
    if (filters.minPrice > 0) {
      filtered = filtered.filter(option => (option.price || 0) >= filters.minPrice);
    }
    if (filters.maxPrice > 0) {
      filtered = filtered.filter(option => (option.price || 0) <= filters.maxPrice);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'price':
          return (a.price || Infinity) - (b.price || Infinity);
        case 'power':
          return (b.power || 0) - (a.power || 0);
        case 'efficiency':
          return (b.efficiency || 0) - (a.efficiency || 0);
        default: // score
          return (b.suitability_score || 0) - (a.suitability_score || 0);
      }
    });

    setFilteredOptions(filtered);
  }, [options, filters]);

  // Calculate filter ranges from available options
  const filterRanges = React.useMemo(() => {
    const powers = options.map(o => o.power || 0).filter(p => p > 0);
    const prices = options.map(o => o.price || 0).filter(p => p > 0);
    const manufacturers = [...new Set(options.map(o => o.manufacturer).filter(Boolean))];

    return {
      powerRange: powers.length > 0 ? [Math.min(...powers), Math.max(...powers)] : [0, 0],
      priceRange: prices.length > 0 ? [Math.min(...prices), Math.max(...prices)] : [0, 0],
      manufacturers
    };
  }, [options]);

  const handleSelect = async () => {
    if (!selectedOption) return;

    setLoading(true);
    try {
      await onSelect(selectedOption);
      addStatusMessage(`Selected ${selectedOption.name}`, 'success');
      onClose();
    } catch (error) {
      console.error('Error selecting component:', error);
      addStatusMessage('Failed to select component', 'error');
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setFilters({
      sortBy: 'score',
      manufacturer: '',
      minPower: 0,
      maxPower: 0,
      minPrice: 0,
      maxPrice: 0
    });
  };

  const getDisplayName = (type: string) => {
    return type.replace('generic_', '').replace('_', ' ').toLowerCase();
  };

  const formatPower = (power?: number) => {
    if (!power) return 'Unknown';
    return power >= 1000 ? `${(power / 1000).toFixed(1)} kW` : `${power} W`;
  };

  const formatPrice = (price?: number) => {
    if (!price) return 'Price unknown';
    return `$${price.toLocaleString()}`;
  };

  const formatEfficiency = (efficiency?: number) => {
    if (!efficiency) return 'Unknown';
    return `${(efficiency * 100).toFixed(1)}%`;
  };

  const getSuitabilityColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Select {getDisplayName(componentType)}
              </h2>
              <p className="text-sm text-gray-600">
                Choose a real component to replace {placeholderCount} placeholder{placeholderCount > 1 ? 's' : ''}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl font-bold"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Sort */}
            <div>
              <label htmlFor="sort" className="block text-sm text-gray-600 mb-1">Sort by:</label>
              <select
                id="sort"
                value={filters.sortBy}
                onChange={(e) => setFilters({ ...filters, sortBy: e.target.value as any })}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="score">Best Match</option>
                <option value="price">Price (Low to High)</option>
                <option value="power">Power (High to Low)</option>
                <option value="efficiency">Efficiency (High to Low)</option>
              </select>
            </div>

            {/* Manufacturer */}
            <div>
              <label htmlFor="manufacturer" className="block text-sm text-gray-600 mb-1">Manufacturer:</label>
              <select
                id="manufacturer"
                value={filters.manufacturer}
                onChange={(e) => setFilters({ ...filters, manufacturer: e.target.value })}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="">All Manufacturers</option>
                {filterRanges.manufacturers.map(manufacturer => (
                  <option key={manufacturer} value={manufacturer}>{manufacturer}</option>
                ))}
              </select>
            </div>

            {/* Power Range */}
            {filterRanges.powerRange[1] > 0 && (
              <div>
                <label className="block text-sm text-gray-600 mb-1">Power Range (W):</label>
                <div className="flex space-x-1">
                  <input
                    type="number"
                    placeholder="Min"
                    value={filters.minPower || ''}
                    onChange={(e) => setFilters({ ...filters, minPower: Number(e.target.value) })}
                    className="w-1/2 text-xs border border-gray-300 rounded px-1 py-1"
                    min={filterRanges.powerRange[0]}
                    max={filterRanges.powerRange[1]}
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={filters.maxPower || ''}
                    onChange={(e) => setFilters({ ...filters, maxPower: Number(e.target.value) })}
                    className="w-1/2 text-xs border border-gray-300 rounded px-1 py-1"
                    min={filterRanges.powerRange[0]}
                    max={filterRanges.powerRange[1]}
                  />
                </div>
              </div>
            )}

            {/* Reset Filters */}
            <div className="flex items-end">
              <button
                onClick={resetFilters}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                Reset Filters
              </button>
            </div>
          </div>

          <div className="mt-2 text-sm text-gray-600">
            Showing {filteredOptions.length} of {options.length} options
          </div>
        </div>

        {/* Options List */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {filteredOptions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">
                {options.length === 0 
                  ? `No ${getDisplayName(componentType)} components available`
                  : 'No components match your filters'
                }
              </p>
              {options.length === 0 ? (
                <button
                  onClick={onUploadMore}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Upload Component Datasheets
                </button>
              ) : (
                <button
                  onClick={resetFilters}
                  className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                >
                  Reset Filters
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredOptions.map((option) => (
                <div
                  key={option.part_number}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedOption?.part_number === option.part_number
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedOption(option)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{option.name}</h3>
                        {option.suitability_score && (
                          <span className={`text-sm font-medium ${getSuitabilityColor(option.suitability_score)}`}>
                            {option.suitability_score.toFixed(0)}% match
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        Part: {option.part_number}
                      </p>
                      {option.manufacturer && (
                        <p className="text-sm text-gray-600">
                          Manufacturer: {option.manufacturer}
                        </p>
                      )}
                    </div>
                    
                    {!option.availability && (
                      <span className="text-sm text-red-600 font-medium">
                        Out of Stock
                      </span>
                    )}
                  </div>
                  
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Power:</span>
                      <div className="font-medium">{formatPower(option.power)}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Price:</span>
                      <div className="font-medium">{formatPrice(option.price)}</div>
                    </div>
                    {option.efficiency && (
                      <div>
                        <span className="text-gray-500">Efficiency:</span>
                        <div className="font-medium">{formatEfficiency(option.efficiency)}</div>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Category:</span>
                      <div className="font-medium">{option.category || 'Unknown'}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <button
              onClick={onUploadMore}
              className="text-blue-600 hover:text-blue-800 text-sm underline"
            >
              Upload More Components
            </button>
            
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleSelect}
                disabled={!selectedOption || loading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Selecting...' : 'Select Component'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComponentSelectionModal;
