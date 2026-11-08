"""99 composition: retain existing services, fix offline vehicle owner identities."""
def install(api):
 from admin84 import install as admin
 from vehicle_trade99 import install as trade
 from horns84 import install as horns
 from factions85 import install as factions
 return factions(horns(trade(admin(api))))
