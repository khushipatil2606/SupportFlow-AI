conversation_state = {}


def get_state(user_id: int) -> dict:
    return conversation_state.get(
        user_id,
        {}
    )


def set_state(
    user_id: int,
    state: dict
):
    conversation_state[user_id] = state


def clear_state(user_id: int):
    conversation_state.pop(
        user_id,
        None
    )