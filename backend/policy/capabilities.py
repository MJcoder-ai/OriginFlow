from backend.schemas.ai import AiActionType

ACTION_REQUIRED_SCOPES = {
    AiActionType.add_component: ["components:create"],
    AiActionType.remove_component: ["components:delete"],
    AiActionType.add_link: ["links:create"],
    AiActionType.remove_link: ["links:delete"],
    AiActionType.update_position: ["layout:update"],
    # Additional mappings can be added here for other action types
}
