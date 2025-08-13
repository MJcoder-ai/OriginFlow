import React, { useState, useEffect } from 'react';
import { useAppStore } from '../appStore';

interface RequirementsFormProps {
  sessionId: string;
  onSubmit: (requirements: DesignRequirements) => void;
  onCancel: () => void;
  initialValues?: Partial<DesignRequirements>;
  isModal?: boolean;
}

interface DesignRequirements {
  target_power?: number;
  roof_area?: number;  
  budget?: number;
  preferred_brands?: string[];
  backup_hours?: number;
  environmental_conditions?: {
    climate_zone?: string;
    wind_speed?: number;
    snow_load?: number;
  };
}

interface FormErrors {
  [key: string]: string;
}

export const RequirementsForm: React.FC<RequirementsFormProps> = ({
  sessionId,
  onSubmit,
  onCancel,
  initialValues = {},
  isModal = false
}) => {
  const [requirements, setRequirements] = useState<DesignRequirements>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { addStatusMessage } = useAppStore();

  // Load existing requirements when component mounts
  useEffect(() => {
    if (sessionId && Object.keys(initialValues).length === 0) {
      loadExistingRequirements();
    }
  }, [sessionId]);

  const loadExistingRequirements = async () => {
    try {
      const response = await fetch(`/api/v1/odl/sessions/${sessionId}/analysis`);
      if (response.ok) {
        const data = await response.json();
        // In a real implementation, this would extract requirements from the analysis
        // For now, we'll just use the initial values
      }
    } catch (error) {
      console.warn('Could not load existing requirements:', error);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!requirements.target_power || requirements.target_power <= 0) {
      newErrors.target_power = 'Target power must be greater than 0';
    } else if (requirements.target_power > 1000000) {
      newErrors.target_power = 'Target power seems unreasonably high';
    }
    
    if (!requirements.roof_area || requirements.roof_area <= 0) {
      newErrors.roof_area = 'Roof area must be greater than 0';
    } else if (requirements.roof_area > 10000) {
      newErrors.roof_area = 'Roof area seems unreasonably large';
    }
    
    if (!requirements.budget || requirements.budget <= 0) {
      newErrors.budget = 'Budget must be greater than 0';
    } else if (requirements.budget < 1000) {
      newErrors.budget = 'Budget may be too low for a solar system';
    }

    if (requirements.backup_hours && requirements.backup_hours < 0) {
      newErrors.backup_hours = 'Backup hours cannot be negative';
    }

    // Validate environmental conditions if provided
    if (requirements.environmental_conditions?.wind_speed && 
        requirements.environmental_conditions.wind_speed < 0) {
      newErrors.wind_speed = 'Wind speed cannot be negative';
    }

    if (requirements.environmental_conditions?.snow_load && 
        requirements.environmental_conditions.snow_load < 0) {
      newErrors.snow_load = 'Snow load cannot be negative';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      // Submit requirements to backend
      const response = await fetch(`/api/v1/odl/sessions/${sessionId}/requirements`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save requirements');
      }
      
      addStatusMessage('Requirements saved successfully', 'success');
      onSubmit(requirements);
    } catch (error) {
      console.error('Error saving requirements:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      addStatusMessage(`Failed to save requirements: ${errorMessage}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBrandInput = (value: string) => {
    const brands = value.split(',').map(s => s.trim()).filter(Boolean);
    setRequirements({
      ...requirements,
      preferred_brands: brands
    });
  };

  const containerClass = isModal 
    ? "max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg max-h-[90vh] overflow-y-auto"
    : "max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-sm";

  return (
    <div className={containerClass}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Design Requirements</h2>
        <p className="text-gray-600 mt-1">
          Specify your solar system requirements to generate an optimized design
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Requirements */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Target Power */}
          <div>
            <label htmlFor="target_power" className="block text-sm font-medium text-gray-700 mb-2">
              Target Power (Watts) *
            </label>
            <input
              type="number"
              id="target_power"
              value={requirements.target_power || ''}
              onChange={(e) => setRequirements({
                ...requirements,
                target_power: parseFloat(e.target.value) || undefined
              })}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.target_power ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="5000"
              min="100"
              max="1000000"
            />
            {errors.target_power && (
              <p className="mt-1 text-sm text-red-600">{errors.target_power}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Typical residential: 3,000-10,000W
            </p>
          </div>

          {/* Roof Area */}
          <div>
            <label htmlFor="roof_area" className="block text-sm font-medium text-gray-700 mb-2">
              Available Roof Area (m²) *
            </label>
            <input
              type="number"
              id="roof_area"
              value={requirements.roof_area || ''}
              onChange={(e) => setRequirements({
                ...requirements,
                roof_area: parseFloat(e.target.value) || undefined
              })}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.roof_area ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="50"
              min="1"
              max="10000"
              step="0.1"
            />
            {errors.roof_area && (
              <p className="mt-1 text-sm text-red-600">{errors.roof_area}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Usable roof space for solar panels
            </p>
          </div>

          {/* Budget */}
          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
              Budget ($) *
            </label>
            <input
              type="number"
              id="budget"
              value={requirements.budget || ''}
              onChange={(e) => setRequirements({
                ...requirements,
                budget: parseFloat(e.target.value) || undefined
              })}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.budget ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="15000"
              min="1000"
            />
            {errors.budget && (
              <p className="mt-1 text-sm text-red-600">{errors.budget}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Total budget including equipment and installation
            </p>
          </div>

          {/* Backup Hours */}
          <div>
            <label htmlFor="backup_hours" className="block text-sm font-medium text-gray-700 mb-2">
              Backup Hours (optional)
            </label>
            <input
              type="number"
              id="backup_hours"
              value={requirements.backup_hours || ''}
              onChange={(e) => setRequirements({
                ...requirements,
                backup_hours: parseFloat(e.target.value) || undefined
              })}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.backup_hours ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="8"
              min="0"
              max="72"
            />
            {errors.backup_hours && (
              <p className="mt-1 text-sm text-red-600">{errors.backup_hours}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Hours of backup power needed during outages
            </p>
          </div>
        </div>

        {/* Preferred Brands */}
        <div>
          <label htmlFor="preferred_brands" className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Brands (optional)
          </label>
          <input
            type="text"
            id="preferred_brands"
            value={requirements.preferred_brands?.join(', ') || ''}
            onChange={(e) => handleBrandInput(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="SunPower, Tesla, LG, Panasonic"
          />
          <p className="mt-1 text-xs text-gray-500">
            Comma-separated list of preferred component brands
          </p>
        </div>

        {/* Advanced Settings Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center text-sm text-blue-600 hover:text-blue-800"
          >
            {showAdvanced ? '▼' : '▶'} Advanced Environmental Conditions
          </button>
        </div>

        {/* Advanced Settings */}
        {showAdvanced && (
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Environmental Conditions</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="climate_zone" className="block text-sm font-medium text-gray-700 mb-2">
                  Climate Zone
                </label>
                <select
                  id="climate_zone"
                  value={requirements.environmental_conditions?.climate_zone || ''}
                  onChange={(e) => setRequirements({
                    ...requirements,
                    environmental_conditions: {
                      ...requirements.environmental_conditions,
                      climate_zone: e.target.value
                    }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select zone</option>
                  <option value="tropical">Tropical</option>
                  <option value="subtropical">Subtropical</option>
                  <option value="temperate">Temperate</option>
                  <option value="continental">Continental</option>
                  <option value="polar">Polar</option>
                </select>
              </div>

              <div>
                <label htmlFor="wind_speed" className="block text-sm font-medium text-gray-700 mb-2">
                  Max Wind Speed (km/h)
                </label>
                <input
                  type="number"
                  id="wind_speed"
                  value={requirements.environmental_conditions?.wind_speed || ''}
                  onChange={(e) => setRequirements({
                    ...requirements,
                    environmental_conditions: {
                      ...requirements.environmental_conditions,
                      wind_speed: parseFloat(e.target.value) || undefined
                    }
                  })}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.wind_speed ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="150"
                  min="0"
                  max="300"
                />
                {errors.wind_speed && (
                  <p className="mt-1 text-sm text-red-600">{errors.wind_speed}</p>
                )}
              </div>

              <div>
                <label htmlFor="snow_load" className="block text-sm font-medium text-gray-700 mb-2">
                  Snow Load (Pa)
                </label>
                <input
                  type="number"
                  id="snow_load"
                  value={requirements.environmental_conditions?.snow_load || ''}
                  onChange={(e) => setRequirements({
                    ...requirements,
                    environmental_conditions: {
                      ...requirements.environmental_conditions,
                      snow_load: parseFloat(e.target.value) || undefined
                    }
                  })}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.snow_load ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="2400"
                  min="0"
                  max="10000"
                />
                {errors.snow_load && (
                  <p className="mt-1 text-sm text-red-600">{errors.snow_load}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex space-x-4 pt-6 border-t border-gray-200">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving...' : 'Save Requirements'}
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Cancel
          </button>
        </div>

        {/* Validation Summary */}
        {Object.keys(errors).length > 0 && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              Please fix the following errors before submitting:
            </p>
            <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
              {Object.values(errors).map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}
      </form>
    </div>
  );
};

export default RequirementsForm;