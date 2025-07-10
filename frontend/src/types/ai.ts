export interface AiAction {
  action: 'addComponent' | 'removeComponent' | 'addLink' | 'removeLink';
  payload: any; // narrow later per schema
  version: number;
}
