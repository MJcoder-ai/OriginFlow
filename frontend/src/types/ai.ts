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
  confidence?: number; // Confidence score from learning agent
  auto_approved?: boolean; // Whether this action was automatically approved
}
