class InclusionExclusionType:
  INCLUSION="INCLUSION"
  EXCLUSION="EXCLUSION"
  CHOICES=(
   (INCLUSION,"Inclusion"),
   (EXCLUSION,"Exclusion"),
  )

class UserRoletype:
    AGENT = "AGENT"
    USER = "USER"
    SUPER_ADMIN = "SUPER_ADMIN"

    CHOICES = (
        (AGENT, "Agent"),
        (USER, "User"),
        (SUPER_ADMIN, "Super Admin"),
    )

class PLAN_STATUS:
  DRAFT="DRAFT"
  CONFIRMED="CONFIRMED"
  SHARED="SHARED"
  ARCHIVED="ARCHIVED"
  CHOICES=(
    (DRAFT,"Draft"),
    (CONFIRMED,"Confirmed"),
    (SHARED,"Shared"),
    (ARCHIVED,"Archived"),
  )

class TravelType:
    GROUP = "GROUP"
    SOLO = "SOLO"
    COUPLE = "COUPLE"

    CHOICES = (
        (GROUP, "Group Tour"),
        (SOLO, "Solo Travel"),
        (COUPLE, "Couple"),
    )

class ValidityMode:
    OPEN = "OPEN"
    DATE_RANGE = "DATE_RANGE"
    MONTH = "MONTH"
    YEAR = "YEAR"

    CHOICES = (
        (OPEN, "Open Validity"),
        (DATE_RANGE, "Date Range"),
        (MONTH, "Month Based"),
        (YEAR, "Year Based"),
    )

class CurrencyType:
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    ISK = "ISK"
    CHF = "CHF"

    CHOICES = [
        (INR, "Indian Rupee"),
        (USD, "US Dollar"),
        (EUR, "Euro"),
        (ISK, "Icelandic Króna"),
        (CHF, "Swiss Franc"),
    ]
class DaySlot:
    MORNING = "MORNING"
    NOON = "NOON"
    NIGHT = "NIGHT"
    FULL_DAY = "FULL_DAY"

    CHOICES = (
        (MORNING, "Morning"),
        (NOON, "Noon"),
        (NIGHT, "Night"),
        (FULL_DAY, "Full Day"),
    )
