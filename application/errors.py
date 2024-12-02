
class WalletError(Exception):
    pass

class ValidationError(Exception):
    pass

class DataNotFound(Exception):
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