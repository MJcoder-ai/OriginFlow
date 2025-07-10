export interface AiAction {
  action:
    | 'addComponent'
    | 'removeComponent'
    | 'addLink'
    | 'removeLink'
    | 'updatePosition'
    | 'suggestLink'
    | 'report';
  payload: any; // narrow later per schema
  version: number;
}
