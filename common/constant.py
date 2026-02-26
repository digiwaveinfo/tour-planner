class InclusionExclusionType:
  INCLUSION="inclusion"
  EXCLUSION="exclusion"
  CHOICES=(
   (INCLUSION,"Inclusion"),
   (EXCLUSION,"Exclusion"),
  )

class UserRoletype:
  AGENT="agent"
  ADMIN="admin"
  CHOICES=(
   (AGENT,"Agent"),
   (ADMIN,"Admin"),
  )

class PLAN_STATUS:
  DRAFT="draft"
  CONFIRMED="confirmed"
  SHARED="shared"
  ARCHIVED="archived"
  CHOICES=(
    ("draft","Draft"),
    ("confirmed","Confirmed"),
    ("shared","Shared"),
    ("archived","Archived"),
  )