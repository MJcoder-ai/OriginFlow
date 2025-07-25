/**
 * File: frontend/src/services/api.ts
 * Centralized service for making API calls to the backend.
 * Provides helper functions to fetch and persist canvas data.
 */
import { CanvasComponent, Link } from '../appStore';
import { AiAction } from '../types/ai';
import { DesignSnapshot } from '../types/analysis';
import { API_BASE_URL } from '../config';

export type ComponentCreateDTO = Omit<CanvasComponent, 'id' | 'ports'>;
/** Payload for creating a link via the backend API. */
export type LinkCreateDTO = Omit<Link, 'id'>;
export const api = {
  async getComponents(): Promise<CanvasComponent[]> {
    const response = await fetch(`${API_BASE_URL}/components/`);
    if (!response.ok) throw new Error('Failed to fetch components');
    return response.json();
  },

  async getLinks(): Promise<Link[]> {
    const response = await fetch(`${API_BASE_URL}/links/`);
    if (!response.ok) throw new Error('Failed to fetch links');
    return response.json();
  },

  async createComponent(componentData: ComponentCreateDTO): Promise<CanvasComponent> {
    const response = await fetch(`${API_BASE_URL}/components/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(componentData),
    });
    if (!response.ok) throw new Error('Failed to create component');
    return response.json();
  },

  async createLink(linkData: LinkCreateDTO): Promise<Link> {
    const response = await fetch(`${API_BASE_URL}/links/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(linkData),
    });
    if (!response.ok) throw new Error('Failed to create link');
    return response.json();
  },

  async updateComponent(
    id: string,
    updateData: Partial<ComponentCreateDTO>
  ): Promise<CanvasComponent> {
    const response = await fetch(`${API_BASE_URL}/components/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData),
    });
    if (!response.ok) throw new Error('Failed to update component');
    return response.json();
  },

  async deleteComponent(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/components/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete component');
  },

  async analyzeDesign(snapshot: DesignSnapshot, command: string): Promise<AiAction[]> {
    const res = await fetch(`${API_BASE_URL}/ai/analyze-design`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, snapshot }),
    });
    if (!res.ok) throw new Error(`Analyze failed: ${res.status}`);
    return res.json();
  },

  /** POST a natural-language command and receive deterministic actions. */
  async sendCommandToAI(command: string): Promise<AiAction[]> {
    const res = await fetch(`${API_BASE_URL}/ai/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`AI endpoint error ${res.status}: ${text.slice(0, 120)}`);
    }
    return res.json();
  },
};
