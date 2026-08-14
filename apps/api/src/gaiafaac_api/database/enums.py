from enum import StrEnum


class VerificationStatus(StrEnum):
    PENDING = "pending"
    AUTOMATICALLY_VALIDATED = "automatically_validated"
    REQUIRES_REVIEW = "requires_review"
    HUMAN_VERIFIED = "human_verified"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EvidenceStatus(StrEnum):
    UNAVAILABLE = "unavailable"
    DETECTED = "detected"
    PENDING_EXTRACTION = "pending_extraction"
    EXTRACTED = "extracted"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    PARTIAL = "partial"
    CONFLICTING = "conflicting"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class EvidenceConflictStatus(StrEnum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class FiscalEventSeverity(StrEnum):
    INFORMATIONAL = "informational"
    NOTABLE = "notable"
    MATERIAL = "material"
    CRITICAL = "critical"


class SourceStatus(StrEnum):
    PENDING = "pending"
    REGISTERED = "registered"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    DEMO = "demo"


class ProcessingStatus(StrEnum):
    REGISTERED = "registered"
    QUEUED = "queued"
    PROCESSING = "processing"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ExtractionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class ComponentType(StrEnum):
    STATUTORY_ALLOCATION = "statutory_allocation"
    VAT = "vat"
    DERIVATION = "derivation"
    EXCHANGE_DIFFERENCE = "exchange_difference"
    AUGMENTATION = "augmentation"
    ELECTRONIC_MONEY_TRANSFER_LEVY = "electronic_money_transfer_levy"
    SOLID_MINERALS = "solid_minerals"
    REFUNDS = "refunds"
    OTHER = "other"


class ReportedUnit(StrEnum):
    NAIRA = "naira"
    THOUSAND_NAIRA = "thousand_naira"
    MILLION_NAIRA = "million_naira"
    BILLION_NAIRA = "billion_naira"
    UNSPECIFIED = "unspecified"


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ForecastMethod(StrEnum):
    SEASONAL_NAIVE = "seasonal_naive"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"


class InsightStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserRole(StrEnum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    ADMINISTRATOR = "administrator"


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PlanCode(StrEnum):
    FREE = "free"
    ANALYST = "analyst"
    TEAM = "team"
    API = "api"
