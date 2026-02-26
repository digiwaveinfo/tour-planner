class InclusionExclusionType:
  INCLUSION="INCLUSION"
  EXCLUSION="EXCLUSION"
  CHOICES=(
   (INCLUSION,"Inclusion"),
   (EXCLUSION,"Exclusion"),
  )

class UserRoletype:
  AGENT="AGENT"
  ADMIN="ADMIN"
  BASIC_USER="BASIC_USER"
  CHOICES=(
   (AGENT,"Agent"),
   (ADMIN,"Admin"),
   (BASIC_USER,"Basic User"),
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