"""Small authoritative extensions composed after the existing city services."""
def install(api):
 from admin84 import install as admin
 from vehicle_trade84 import install as trade
 from horns84 import install as horns
 from factions85 import install as factions
 return factions(horns(trade(admin(api))))
