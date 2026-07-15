"""Safety checker for V.E.R.A. — optional action validation."""

from utils.logger import get_logger

logger = get_logger("vera.engine")


class SafetyChecker:
    """Validates actions before execution. Unrestricted mode by default."""

    def __init__(self, config: dict):
        self.confirm_before_exec = config.get("confirm_before_exec", False)
        self.blocked_commands = config.get("blocked_commands", [])
        self.log_all_actions = config.get("log_all_actions", True)

    def check(self, action_type: str, action: dict) -> dict:
        if self._is_blocked(action_type, action):
            logger.warning(f"Blocked action: {action_type} - {action}")
            return {"allowed": False, "reason": "This action is on the blocked list."}
        if self.log_all_actions:
            logger.info(f"Action approved: {action_type} - {action}")
        return {"allowed": True, "requires_confirmation": self.confirm_before_exec}

    def _is_blocked(self, action_type: str, action: dict) -> bool:
        if not self.blocked_commands:
            return False
        action_str = str(action).lower()
        for blocked in self.blocked_commands:
            if blocked.lower() in action_str:
                return True
        return False
