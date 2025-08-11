import React, { useState } from 'react';
import { useAppStore } from '../appStore';

const RequirementsForm: React.FC = () => {
  const current = useAppStore((s) => s.requirements);
  const updateRequirements = useAppStore((s) => s.updateRequirements);
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

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = {};
    if (targetPower) payload.target_power = Number(targetPower);
    if (roofArea) payload.roof_area = Number(roofArea);
    if (budget) payload.budget = Number(budget);
    if (brand) payload.brand = brand;
    await updateRequirements(payload);
  };

  return (
    <form onSubmit={onSubmit} className="mt-3 p-3 border rounded bg-white">
      <div className="text-xs font-semibold uppercase text-gray-600 mb-2">Requirements</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="flex flex-col text-sm">
          <span className="text-gray-600 mb-1">Target power (kW)</span>
          <input
            type="number"
            value={targetPower}
            onChange={(e) => setTargetPower(e.target.value)}
            min={0}
            step={0.1}
            className="border rounded px-2 py-1"
            placeholder="e.g. 5"
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="text-gray-600 mb-1">Roof area (m²)</span>
          <input
            type="number"
            value={roofArea}
            onChange={(e) => setRoofArea(e.target.value)}
            min={0}
            step={0.1}
            className="border rounded px-2 py-1"
            placeholder="e.g. 30"
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="text-gray-600 mb-1">Budget</span>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            min={0}
            step={100}
            className="border rounded px-2 py-1"
            placeholder="e.g. 10000"
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="text-gray-600 mb-1">Preferred brand</span>
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="e.g. Any"
          />
        </label>
      </div>
      <div className="mt-3 flex justify-end">
        <button type="submit" className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">
          Save & Refresh Plan
        </button>
      </div>
    </form>
  );
};

export default RequirementsForm;


