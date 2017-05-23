var regex_in_template = {};

regex_in_template["../test/fixtures/pattern.tpl.html"] = "<form>\n" +
   "<span class=\"registration-error\" ng-show=\"regForm.password.$error.pattern\">- Fail to match..</span>\n" +
   "<input type=\"password\" ng-model=\"registerForm.password\" name=\"password\" ng-pattern=\"/^.*(?=.{8,})(?=.*[a-z])(?=.*[A-Z])(?=.*[\\d\\W]).*$/\"  required/>\n" +
   "</form>\n" +
   "";
