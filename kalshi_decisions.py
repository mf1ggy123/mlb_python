class KalshiEvent:
    def __init__(self, event_params, exchange_client):
        self.event_params = event_params
        self.exchange_client = exchange_client

    def get_event(self):
        return self.exchange_client.get_event(**self.event_params)