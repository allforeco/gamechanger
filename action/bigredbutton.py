import os

class BigRedButton():
  EMERGENCYFILENAME = 'emergency.stop'
  def emergency_activate():
    if not BigRedButton.is_emergency():
      ef = open(BigRedButton.EMERGENCYFILENAME, "x")
      ef.write("this file prevents functions in case of emergencies")
      ef.close()
    return
  
  def emergency_deactivate():
    if BigRedButton.is_emergency():
      os.remove(BigRedButton.EMERGENCYFILENAME)
    return

  def is_emergency():
    em = os.path.isfile(BigRedButton.EMERGENCYFILENAME)
    return em