import re

replacement_patterns = [
  (r'Agricultural and Biological Engineering', 'Agricultural and Biosystems Engineering'),
  (r'Industrial Engineering', 'Industrial and Manufacturing Systems Engineering'),
  (r'Materials Science & Engineering', 'Materials Science and Engineering'),
  (r'Molecular, Cellular, and Developmental Biology', 'Molecular, Cellular and Developmental Biology'),
  (r'Education Leadership', 'Education'),
  (r'Agriculture Engineering', 'Agricultural and Biosystems Engineering'),
  (r'Agricultural Engineering', 'Agricultural and Biosystems Engineering'),
  (r'Materials Science', 'Materials Science and Engineering'),
  (r'Electrical and Computer Engineering', 'Computer Engineering'),
  (r'Nutritional Science', 'Nutritional Sciences')
]

abbreviation_replacement = [
(r'M.F.C.S.' , 'http://lib.iastate.edu/#degrees-MasterofFamilyandConsumerSciences'),
(r'M.C.R.P.' , 'http://lib.iastate.edu/#degrees-MasterofCommunityandRegionalPlanning'),
(r'M.Engr.' , 'http://lib.iastate.edu/#degrees-MasterofEngineering'),
(r'M.Arch.' , 'http://lib.iastate.edu/#degrees-MasterofArchitecture'),
(r'M.Educ.' , 'http://lib.iastate.edu/#degrees-MasterofEducation'),
(r'M.L.A.' , 'http://lib.iastate.edu/#degrees-MasterofLandscapeArchitecture'),
(r'M.P.A.' , 'http://lib.iastate.edu/#degrees-MasterofPublicAdministration'),
(r'M.B.A.' , 'http://lib.iastate.edu/#degrees-MasterofBusinessAdministration'),
(r'M.S.M.' , 'http://lib.iastate.edu/#degrees-MasterofSchoolMathematics'),
(r'M.Acc.' , 'http://lib.iastate.edu/#degrees-MasterofAccounting'),
(r'M.A.T.' , 'http://lib.iastate.edu/#degrees-MasterofArtsinTeaching'),
(r'M.F.A.' , 'http://lib.iastate.edu/#degrees-MasterofFineArts'),
(r'M.Ed.' , 'http://lib.iastate.edu/#degrees-MasterofEducation'),
(r'M.Ag.' , 'http://lib.iastate.edu/#degrees-MasterofAgriculture'),
(r'Ph.D.' , 'http://lib.iastate.edu/#degrees-DoctorofPhilosophy'),
(r'M.A.' , 'http://lib.iastate.edu/#degrees-MasterofArts'),
(r'B.S.' , 'http://lib.iastate.edu/#degrees-BachelorofScience'),
(r'M.E.' , 'http://lib.iastate.edu/#degrees-MasterofEngineering'),
(r'M.S.' , 'http://lib.iastate.edu/#degrees-MasterofScience'),
(r'Sp.' , 'http://lib.iastate.edu/#degrees-Specialist')
]


class RegexpReplacer(object):
  def __init__(self, patterns=replacement_patterns):
    self.patterns = [(re.compile(regex), repl) for (regex, repl) in
      patterns]

  def replace(self, text):
    s = text
    for (pattern, repl) in self.patterns:
      s = re.sub(pattern, repl, s)
    return s
