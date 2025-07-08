/**
 * File: frontend/src/services/api.ts
 * Centralized service for making API calls to the backend.
 * Provides helper functions to fetch and persist canvas data.
 */
import { CanvasComponent, Link } from '../appStore';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export type ComponentCreateDTO = Omit<CanvasComponent, 'id' | 'ports'>;
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
};
