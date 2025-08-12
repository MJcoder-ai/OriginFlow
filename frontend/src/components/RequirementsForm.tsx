import React, { useState } from 'react';
import { useAppStore } from '../appStore';
import { Upload, FileText, Plus, Minus, Save, RefreshCw } from 'lucide-react';

const RequirementsForm: React.FC = () => {
  const current = useAppStore((s) => s.requirements);
  const updateRequirements = useAppStore((s) => s.updateRequirements);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Basic requirements
  const [targetPower, setTargetPower] = useState<string>(
    current.target_power != null ? String(current.target_power) : ''
  );
  const [roofArea, setRoofArea] = useState<string>(
    current.roof_area != null ? String(current.roof_area) : ''
  );
  const [budget, setBudget] = useState<string>(
    current.budget != null ? String(current.budget) : ''
  );
  const [brand, setBrand] = useState<string>(current.brand ?? '');
  
  // Advanced requirements
  const [installationType, setInstallationType] = useState('ground_mount');
  const [customRequirements, setCustomRequirements] = useState<Array<{key: string, value: string}>>([]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload: any = {};
      if (targetPower) payload.target_power = Number(targetPower);
      if (roofArea) payload.roof_area = Number(roofArea);
      if (budget) payload.budget = Number(budget);
      if (brand) payload.brand = brand;
      if (installationType) payload.installation_type = installationType;
      
      // Add custom requirements
      customRequirements.forEach(req => {
        if (req.key && req.value) {
          payload[req.key] = req.value;
        }
      });
      
      await updateRequirements(payload);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const addCustomRequirement = () => {
    setCustomRequirements([...customRequirements, { key: '', value: '' }]);
  };
  
  const removeCustomRequirement = (index: number) => {
    setCustomRequirements(customRequirements.filter((_, i) => i !== index));
  };
  
  const updateCustomRequirement = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...customRequirements];
    updated[index][field] = value;
    setCustomRequirements(updated);
  };

  return (
    <div className="mt-3 border rounded-lg bg-white shadow-sm">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <FileText className="w-4 h-4 mr-2" />
            Project Requirements
          </h3>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
          </button>
        </div>
      </div>
      
      <form onSubmit={onSubmit} className="p-4 space-y-4">
        {/* Basic Requirements */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Target Power (kW) *
            </label>
            <input
              type="number"
              value={targetPower}
              onChange={(e) => setTargetPower(e.target.value)}
              min={0}
              step={0.1}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g. 5.0"
              required
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Available Area (m²)
            </label>
            <input
              type="number"
              value={roofArea}
              onChange={(e) => setRoofArea(e.target.value)}
              min={0}
              step={0.1}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g. 30.0"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Budget (USD)
            </label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              min={0}
              step={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g. 10000"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Preferred Brand
            </label>
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g. Tesla, SunPower, etc."
            />
          </div>
        </div>
        
        {/* Advanced Requirements */}
        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t border-gray-100">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Installation Type
              </label>
              <select
                value={installationType}
                onChange={(e) => setInstallationType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="roof_mount">Roof Mount</option>
                <option value="ground_mount">Ground Mount</option>
                <option value="carport">Carport</option>
                <option value="floating">Floating</option>
              </select>
            </div>
            
            {/* Custom Requirements */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Custom Requirements
                </label>
                <button
                  type="button"
                  onClick={addCustomRequirement}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Custom
                </button>
              </div>
              
              {customRequirements.map((req, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={req.key}
                    onChange={(e) => updateCustomRequirement(index, 'key', e.target.value)}
                    placeholder="Property name"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <input
                    type="text"
                    value={req.value}
                    onChange={(e) => updateCustomRequirement(index, 'value', e.target.value)}
                    placeholder="Value"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => removeCustomRequirement(index)}
                    className="p-2 text-red-600 hover:text-red-800"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Submit Button */}
        <div className="flex justify-end pt-4 border-t border-gray-100">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save & Refresh Plan
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RequirementsForm;


