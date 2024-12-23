
class WalletError(Exception):
    pass

class ValidationError(Exception):
    pass

class ContextValidationError(Exception):
    pass

class DataNotFound(Exception):
    pass

class DataAlreadyExists(Exception):
    pass

class InvalidUserData(Exception):
    pass

class UserAuthenticationFailure(Exception):
    pass

class UserAuthenticationRequired(Exception):
    pass

class InvoiceCreationError(Exception):
    pass

class InvoiceBadStateError(Exception):
    pass

class PaymentProcessingError(Exception):
    pass

class PaymentCreationError(Exception):
    pass

class PaymentContextValidationError(Exception):
    pass

class UserActionRequiredError(Exception):
    pass

class OrderProcessing(Exception):
    def __init__(self, schedule: int) -> None:
        self.schedule = schedule

    def get_next_schedule(self) -> int:
        return self.schedule

class OrderFulfilled(Exception):
    pass

class UnexpectedStatus(Exception):
    pass