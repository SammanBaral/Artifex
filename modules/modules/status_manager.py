class StatusManager:
    _status = "idle"

    @classmethod
    def set_status(cls, status):
        cls._status = status
        print(f"Status updated to: {cls._status}")  # For debugging

    @classmethod
    def get_status(cls):
        return cls._status

status_manager = StatusManager()